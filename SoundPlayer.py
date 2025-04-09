"""
SoundPlayer.py
Play WAV files or tones using an I2S DAC amplifier
Originally from mteachman's i2s-examples git repository
Combined playTone and SoundPlayer to have a single
non-blocking Sound Player class

Original full license is included below.
"""


# The MIT License (MIT)
# Copyright (c) 2022-2024 Mike Teachman
# https://opensource.org/licenses/MIT
#
# MicroPython Class used to control playing a WAV file or a generated tone
# using an I2S amplifier or DAC module
# - control playback with 5 methods:
#     - play() / playTone()
#     - pause()
#     - resume()
#     - stop()
#     - isplaying()
#
# Example (WAV):
#    wp = SoundPlayer(...)
#    wp.play("YOUR_WAV_FILE.wav", loop=True)
#
# Example (Tone):
#    wp = SoundPlayer(...)
#    wp.playTone(frequency=440, duration_ms=-1) # Play 440Hz indefinitely
#
# All methods are non-blocking.

import os
import struct
import math
from machine import I2S, Pin
from Log import *

class SoundPlayer:
    """
    A SoundPlayer class capable of playing mono and stereo wav files
    up to 16 bits and 16k from flash or SDCard, as well as playing
    any tone with a specific frequency.
    
    All playback is non-blocking, and can be controlled via
    play, pause, resume, stop controls.
    """
    
    # Playback states
    PLAY = 0
    PAUSE = 1
    RESUME = 2
    FLUSH = 3
    STOP = 4

    # Data source types
    _TYPE_NONE = 0
    _TYPE_WAV = 1
    _TYPE_TONE = 2

    # Default tone generation parameters
    _DEFAULT_TONE_SAMPLE_RATE = 22050
    _DEFAULT_TONE_BITS_PER_SAMPLE = 16
    _DEFAULT_TONE_FORMAT = I2S.MONO

    def __init__(self, id, sck_pin, ws_pin, sd_pin, ibuf=1000, root="/"):
        """
        Initialize the player. Provide the correct pins.
        Note that sd_pin has to be adjacent to the ws_pin (+1)
        
        Also, on the Raspberry Pi Pico, the sck pin needs to be connected to ground
        use the bck pin as sck_pin, din and lck as ws_pin and sd_pin respectively
        """
        
        self.id = id
        self.sck_pin = sck_pin
        self.ws_pin = ws_pin
        self.sd_pin = sd_pin
        self.ibuf = ibuf
        self.root = root.rstrip("/") + "/"

        self.state = SoundPlayer.STOP
        self.audio_out = None
        self._playback_type = SoundPlayer._TYPE_NONE

        # --- WAV specific ---
        self.wav = None
        self.loop = False
        self.first_sample_offset = 0

        # --- Tone specific ---
        self._tone_buffer = None
        self._tone_buffer_offset = 0
        self._tone_samples_per_cycle = 0
        self._tone_total_samples_to_play = 0 # For duration control
        self._tone_samples_played = 0

        # --- Common ---
        self.format = None
        self.sample_rate = None
        self.bits_per_sample = None
        self.num_read = 0  # Bytes read/generated in last callback
        self.sbuf = 1000 # Size of silence buffer chunk
        self.nflush = 0

        # allocate a small array of blank audio samples used for silence
        self.silence_samples = bytearray(self.sbuf)

        # allocate audio sample array buffer (used for both WAV reading and tone chunking)
        # Make it large enough for efficient I2S transfers
        self._chunk_buffer_size = 4096 # Adjust as needed
        self.samples_mv = memoryview(bytearray(self._chunk_buffer_size))

        # Initialize volume control variable (0.0 to 1.0)
        self.volume = 1.0
        self.volume_int = 256  # 256 corresponds to 1.0 in fixed-point representation

    def setVolume(self, volume):
        """
        Change the volume of playback. volume is between 0.0 and 1.0
        Note that changing volume while a wav is playing might reset
        the playback.
        """
        
        if 0 <= volume <= 1:
            self.volume = volume
            self.volume_int = int(volume * 256)  # Scale to 0-256
        else:
            raise ValueError("Volume must be between 0.0 and 1.0")

    def play(self, wav_file_path, loop=False):
        """
        Plays a WAV file.
        If playback is already active (playing or paused), it will be
        stopped cleanly before the new WAV file starts.
        """
        # If already playing or paused, stop the current playback first
        if self.state != SoundPlayer.STOP:
            Log.d("Playback active, stopping current sound...")
            self._stop_playback() # Clean up existing resources
            # _stop_playback should set state to STOP, but ensure it just in case
            self.state = SoundPlayer.STOP
            # Add a small delay if needed, though usually not necessary
            # time.sleep_ms(10)

        full_path = self.root + wav_file_path

        # MicroPython compatible file existence check:
        try:
            file_stat = os.stat(full_path)
            if file_stat[0] & 0x4000:
                 raise ValueError(f"Path '{wav_file_path}' is a directory, not a file.")
            self.wav = open(full_path, "rb")
        except OSError as e:
             raise ValueError(f"WAV file '{wav_file_path}' not found or cannot be opened at '{full_path}'. Error: {e}") from e

        # --- Rest of the play method remains the same ---
        try:
            # File is now open in self.wav
            self._parse_wav_header(self.wav) # Sets rate, bits, format

            self.loop = loop
            self._playback_type = SoundPlayer._TYPE_WAV

            # This will deinit existing I2S if necessary and re-configure
            self._configure_i2s()

            # Seek to the start of audio data
            _ = self.wav.seek(self.first_sample_offset)

            self._start_playback()

        except Exception as e:
            Log.e(f"Error playing WAV: {e}")
            # Ensure cleanup even if setup fails after stopping previous sound
            if self.wav:
                self.wav.close()
                self.wav = None
            if self.audio_out:
                 try: # Might already be deinitialized by _stop_playback
                     self.audio_out.deinit()
                 except Exception: pass
                 self.audio_out = None
            self.state = SoundPlayer.STOP
            self._playback_type = SoundPlayer._TYPE_NONE
            raise # Re-raise the exception


    def playTone(self, frequency, duration_ms=-1,
                  sample_rate=_DEFAULT_TONE_SAMPLE_RATE,
                  bits_per_sample=_DEFAULT_TONE_BITS_PER_SAMPLE,
                  format=_DEFAULT_TONE_FORMAT):
        """
        Plays a generated pure tone.
        If playback is already active (playing or paused), it will be
        stopped cleanly before the new tone starts.
        """
        # If already playing or paused, stop the current playback first
        if self.state != SoundPlayer.STOP:
            Log.d("Playback active, stopping current sound...")
            self._stop_playback() # Clean up existing resources
            # _stop_playback should set state to STOP, but ensure it just in case
            self.state = SoundPlayer.STOP
            # Add a small delay if needed, though usually not necessary
            # time.sleep_ms(10)

        if format != I2S.MONO:
            Log.d("Warning: Tone generation currently only supports MONO.")
            self.format = I2S.MONO
        else:
            self.format = format

        self.sample_rate = sample_rate
        self.bits_per_sample = bits_per_sample
        self.loop = False # Loop concept doesn't apply directly, duration handles it

        try:
            self._make_tone(self.sample_rate, self.bits_per_sample, frequency)
            self._playback_type = SoundPlayer._TYPE_TONE
            self._tone_buffer_offset = 0
            self._tone_samples_played = 0

            if duration_ms == -1: # Play indefinitely
                 self._tone_total_samples_to_play = 0
            elif duration_ms > 0:
                 self._tone_total_samples_to_play = int((self.sample_rate / 1000) * duration_ms)
            else: # duration <= 0 but not -1 means play nothing
                 self._tone_total_samples_to_play = 0
                 Log.d("Tone duration is zero or negative, nothing to play.")
                 self._playback_type = SoundPlayer._TYPE_NONE
                 return # Exit early

            # This will deinit existing I2S if necessary and re-configure
            self._configure_i2s()
            self._start_playback()

        except Exception as e:
            Log.e(f"Error playing tone: {e}")
            # Ensure cleanup even if setup fails after stopping previous sound
            self._tone_buffer = None # Clear buffer on error
            if self.audio_out:
                 try: # Might already be deinitialized by _stop_playback
                     self.audio_out.deinit()
                 except Exception: pass
                 self.audio_out = None
            self.state = SoundPlayer.STOP
            self._playback_type = SoundPlayer._TYPE_NONE
            raise # Re-raise the exception

    def isplaying(self):
        """Returns True if actively playing or paused, False if stopped."""
        return self.state != SoundPlayer.STOP
    
    def resume(self):
        """Resumes paused playback."""
        if self.state != SoundPlayer.PAUSE:
            # Allow resuming if stopped? Maybe not, stick to original logic.
            Log.e("Warning: Playback not paused.")
            return
            # raise ValueError("Playback is not paused.")
        Log.i("Resuming playback.")
        self.state = SoundPlayer.RESUME
        # Callback will transition state back to PLAY

    def pause(self):
        """Pauses active playback."""
        if self.state == SoundPlayer.PAUSE:
            Log.e("Playback already paused.")
            return
        if self.state != SoundPlayer.PLAY:
            Log.e("Warning: Playback not active.")
            return
            # raise ValueError("Playback is not active.")
        Log.i("Pausing playback.")
        self.state = SoundPlayer.PAUSE
        # Callback will start writing silence

    def stop(self):
        """Stops playback and cleans up resources."""
        if self.state == SoundPlayer.STOP:
            Log.d("Playback already stopped.")
            return

        Log.i("Stopping playback...")
        if self.state == SoundPlayer.PLAY or self.state == SoundPlayer.PAUSE or self.state == SoundPlayer.RESUME:
            # Transition to FLUSH state to allow buffer to clear
            self.state = SoundPlayer.FLUSH
            # The callback will handle the rest (calling _stop_playback)
        else:
             # If in another state (e.g., already flushing), force cleanup
             self._stop_playback()
             self.state = SoundPlayer.STOP

    def _make_tone(self, rate, bits, frequency):
        """Generates a single cycle of a sine wave tone."""
        if rate <= frequency or frequency <= 0:
             raise ValueError("Frequency must be > 0 and < rate/2")
        self._tone_samples_per_cycle = rate // frequency
        sample_size_in_bytes = bits // 8
        self._tone_buffer = bytearray(self._tone_samples_per_cycle * sample_size_in_bytes)
        # Increased volume compared to original playTone.py, adjust volume using setVolume()
        # Volume now controlled by self.volume_int during playback
        range_val = pow(2, bits - 1) - 1 # Max amplitude for signed integer

        if bits == 16:
            format_type = "<h" # Signed short
        elif bits == 32:
             format_type = "<l" # Signed long
        else:
            raise ValueError("Unsupported bit depth for tone generation")

        for i in range(self._tone_samples_per_cycle):
            sample = int(range_val * math.sin(2 * math.pi * i / self._tone_samples_per_cycle))
            struct.pack_into(format_type, self._tone_buffer, i * sample_size_in_bytes, sample)

        Log.d(f"Generated tone: {frequency}Hz, {self._tone_samples_per_cycle} samples/cycle, {len(self._tone_buffer)} bytes")

    @micropython.viper
    def adjust_volume_16bit(self, data_in: ptr8, length: int, volume_int: int):
        """Adjusts volume of 16-bit signed PCM data using fixed-point multiplication."""
        data = ptr8(data_in)
        n = int(length // 2)
        for i in range(n):
            # Read two bytes (little-endian) into signed 16-bit
            sample_val = int(data[2 * i]) | (int(data[2 * i + 1]) << 8)
            if sample_val >= 32768: # Sign extend negative numbers
                sample_val -= 65536

            # Adjust volume (fixed point multiply, then shift back)
            sample_val = (sample_val * volume_int) >> 8

            # Clip to int16 range
            if sample_val > 32767:
                sample_val = 32767
            elif sample_val < -32768:
                sample_val = -32768

            # Store back into data buffer (little-endian)
            data[2 * i] = sample_val & 0xFF
            data[2 * i + 1] = (sample_val >> 8) & 0xFF

    # @micropython.viper # Viper might be harder with the modulo arithmetic, implement standard first
    def _get_tone_chunk(self, buffer_mv: memoryview):
        """Fills the buffer_mv with the next chunk of tone data."""
        buffer_len = len(buffer_mv)
        tone_len = len(self._tone_buffer)
        byte_count = 0

        # Optimization: If buffer is larger than tone cycle, copy full cycles first
        while byte_count + tone_len - self._tone_buffer_offset <= buffer_len:
             remaining_in_cycle = tone_len - self._tone_buffer_offset
             buffer_mv[byte_count : byte_count + remaining_in_cycle] = memoryview(self._tone_buffer)[self._tone_buffer_offset:]
             byte_count += remaining_in_cycle
             self._tone_buffer_offset = 0 # Reset offset to start of cycle

        # Copy remaining part needed to fill the buffer
        if byte_count < buffer_len:
            needed = buffer_len - byte_count
            if self._tone_buffer_offset + needed <= tone_len:
                # Copy a contiguous block from the tone buffer
                buffer_mv[byte_count:] = memoryview(self._tone_buffer)[self._tone_buffer_offset : self._tone_buffer_offset + needed]
                self._tone_buffer_offset += needed
            else:
                 # Wrap around: copy remaining part to end, then from beginning
                 part1_len = tone_len - self._tone_buffer_offset
                 buffer_mv[byte_count : byte_count + part1_len] = memoryview(self._tone_buffer)[self._tone_buffer_offset:]
                 part2_len = needed - part1_len
                 buffer_mv[byte_count + part1_len :] = memoryview(self._tone_buffer)[:part2_len]
                 self._tone_buffer_offset = part2_len # New offset is start + part2_len

        # Check duration limit
        if self._tone_total_samples_to_play > 0:
            sample_size = self.bits_per_sample // 8
            samples_in_chunk = buffer_len // sample_size
            remaining_samples = self._tone_total_samples_to_play - self._tone_samples_played
            if samples_in_chunk > remaining_samples:
                # This chunk contains the end of the tone
                bytes_to_keep = remaining_samples * sample_size
                self._tone_samples_played += remaining_samples # Mark as finished
                return bytes_to_keep # Return actual bytes for this last chunk
            else:
                 self._tone_samples_played += samples_in_chunk

        return buffer_len # Return number of bytes placed in buffer

    def i2s_callback(self, arg):
        if self.state == SoundPlayer.PLAY:
            bytes_to_write = 0
            if self._playback_type == SoundPlayer._TYPE_WAV:
                self.num_read = self.wav.readinto(self.samples_mv)
                if self.num_read == 0: # End of WAV file
                    if not self.loop:
                        self.state = SoundPlayer.FLUSH
                        self._playback_type = SoundPlayer._TYPE_NONE # Prepare for stop
                    else:
                        # Loop: Seek back to the start of audio data
                        _ = self.wav.seek(self.first_sample_offset)
                        self.num_read = self.wav.readinto(self.samples_mv) # Read first chunk after looping
                        if self.num_read == 0: # Handle empty or very short looped files
                            self.state = SoundPlayer.FLUSH
                            self._playback_type = SoundPlayer._TYPE_NONE
                            _ = self.audio_out.write(self.silence_samples) # Write silence on error/empty loop
                            return

                    if self.state == SoundPlayer.FLUSH: # Check again if state changed to FLUSH
                         _ = self.audio_out.write(self.silence_samples)
                         return # Exit callback

                bytes_to_write = self.num_read

            elif self._playback_type == SoundPlayer._TYPE_TONE:
                # Check duration limit before generating chunk
                if self._tone_total_samples_to_play > 0 and self._tone_samples_played >= self._tone_total_samples_to_play:
                     self.state = SoundPlayer.FLUSH
                     self._playback_type = SoundPlayer._TYPE_NONE # Prepare for stop
                     _ = self.audio_out.write(self.silence_samples)
                     return

                self.num_read = self._get_tone_chunk(self.samples_mv)
                bytes_to_write = self.num_read

                # Check duration limit *after* generating chunk (in case it ended exactly)
                if self._tone_total_samples_to_play > 0 and self._tone_samples_played >= self._tone_total_samples_to_play:
                     self.state = SoundPlayer.FLUSH
                     self._playback_type = SoundPlayer._TYPE_NONE # Prepare for stop
                     # Write only the valid part of the last chunk
                     if bytes_to_write > 0:
                          if self.bits_per_sample == 16:
                              self.adjust_volume_16bit(self.samples_mv, bytes_to_write, self.volume_int)
                          _ = self.audio_out.write(self.samples_mv[:bytes_to_write])
                     _ = self.audio_out.write(self.silence_samples) # Start flushing
                     return


            # --- Common processing for both WAV and Tone ---
            if bytes_to_write > 0:
                # Apply volume adjustment
                if self.bits_per_sample == 16: # Add checks for other bit depths if needed
                    self.adjust_volume_16bit(self.samples_mv, bytes_to_write, self.volume_int)
                # Write the data
                _ = self.audio_out.write(self.samples_mv[:bytes_to_write])
            else:
                 # If loop resulted in 0 bytes or some other issue, write silence
                 _ = self.audio_out.write(self.silence_samples)


        elif self.state == SoundPlayer.RESUME:
            self.state = SoundPlayer.PLAY
            _ = self.audio_out.write(self.silence_samples) # Write silence to restart hardware

        elif self.state == SoundPlayer.PAUSE:
            _ = self.audio_out.write(self.silence_samples) # Keep feeding silence

        elif self.state == SoundPlayer.FLUSH:
            # Allow residual samples in I2S buffer to play out
            if self.nflush > 0:
                self.nflush -= 1
                _ = self.audio_out.write(self.silence_samples)
            else:
                # Cleanup after flush
                self._stop_playback() # Call helper to deinit and close file
                self.state = SoundPlayer.STOP

        elif self.state == SoundPlayer.STOP:
            # Should ideally not be called in STOP state, but write silence just in case
            _ = self.audio_out.write(self.silence_samples)

        else:
            Log.e(f"Error: Unknown state {self.state} in i2s_callback")
            self.state = SoundPlayer.STOP
            _ = self.audio_out.write(self.silence_samples)

    def _parse_wav_header(self, wav_file):
        """Parses the WAV file header."""
        chunk_ID = wav_file.read(4)
        if chunk_ID != b"RIFF":
            raise ValueError("Invalid WAV file: RIFF chunk ID not found")
        chunk_size = wav_file.read(4) # Total size - 8 bytes, not usually needed
        format_chunk = wav_file.read(4)
        if format_chunk != b"WAVE":
            raise ValueError("Invalid WAV file: WAVE format not found")

        sub_chunk1_ID = wav_file.read(4)
        # Skip extra chunks like 'LIST' if present before 'fmt '
        while sub_chunk1_ID != b"fmt ":
            sub_chunk1_size = struct.unpack("<I", wav_file.read(4))[0]
            wav_file.read(sub_chunk1_size) # Skip this chunk
            sub_chunk1_ID = wav_file.read(4)
            if not sub_chunk1_ID: # End of file reached unexpectedly
                 raise ValueError("Invalid WAV file: fmt chunk not found")

        # Now we are at the 'fmt ' chunk
        sub_chunk1_size = struct.unpack("<I", wav_file.read(4))[0]
        # Read fmt chunk data
        audio_format = struct.unpack("<H", wav_file.read(2))[0]
        num_channels = struct.unpack("<H", wav_file.read(2))[0]
        self.sample_rate = struct.unpack("<I", wav_file.read(4))[0]
        byte_rate = struct.unpack("<I", wav_file.read(4))[0]
        block_align = struct.unpack("<H", wav_file.read(2))[0]
        self.bits_per_sample = struct.unpack("<H", wav_file.read(2))[0]

        # Check for supported formats (PCM, MONO/STEREO, 16/32 bit)
        if audio_format != 1: # 1 = PCM
             raise ValueError("Unsupported WAV format: Only PCM is supported")
        if num_channels == 1:
            self.format = I2S.MONO
        elif num_channels == 2:
            self.format = I2S.STEREO
        else:
            raise ValueError("Unsupported WAV format: Only MONO or STEREO is supported")
        if self.bits_per_sample not in [16, 32]:
             raise ValueError("Unsupported WAV format: Only 16 or 32 bits per sample are supported")

        # Skip potential extra fmt chunk data (if sub_chunk1_size > 16)
        if sub_chunk1_size > 16:
            wav_file.read(sub_chunk1_size - 16)

        # Find the 'data' sub-chunk
        sub_chunk2_ID = wav_file.read(4)
        while sub_chunk2_ID != b"data":
            sub_chunk2_size = struct.unpack("<I", wav_file.read(4))[0]
            wav_file.read(sub_chunk2_size) # Skip chunk
            sub_chunk2_ID = wav_file.read(4)
            if not sub_chunk2_ID: # End of file reached unexpectedly
                 raise ValueError("Invalid WAV file: data chunk not found")

        # Data chunk size (useful for knowing audio data length)
        # data_chunk_size = struct.unpack("<I", wav_file.read(4))[0]

        # Current position is the start of the actual audio data
        self.first_sample_offset = wav_file.tell()

    def _configure_i2s(self):
        """Initializes or reinitializes the I2S peripheral."""
        if self.audio_out:
            self.audio_out.deinit() # Deinitialize if already exists

        Log.i(f"Configuring I2S: rate={self.sample_rate}, bits={self.bits_per_sample}, format={('MONO' if self.format == I2S.MONO else 'STEREO')}")
        self.audio_out = I2S(
            self.id,
            sck=self.sck_pin,
            ws=self.ws_pin,
            sd=self.sd_pin,
            mode=I2S.TX,
            bits=self.bits_per_sample,
            format=self.format,
            rate=self.sample_rate,
            ibuf=self.ibuf,
        )
        # Set up the IRQ callback
        self.audio_out.irq(self.i2s_callback)
        # Calculate necessary flushes based on I2S buffer and silence chunk size
        # Add 1 to ensure buffer is fully cleared
        self.nflush = (self.ibuf // self.sbuf) + 1

    def _start_playback(self):
        """Common actions to start playback after configuration."""
        self.state = SoundPlayer.PLAY
        # Write silence initially to kick off the I2S callback mechanism
        _ = self.audio_out.write(self.silence_samples)
        Log.d("Playback started.")

    def _stop_playback(self):
        """Internal helper to close file/buffer and deinit I2S."""
        Log.d("Performing cleanup...")
        if self.audio_out:
            # Explicitly disable the IRQ before deinit
            try:
                 self.audio_out.irq(None)
            except Exception as e:
                 Log.e(f"Minor issue disabling IRQ: {e}") # Ignore if already deinitialized
            self.audio_out.deinit()
            self.audio_out = None
            Log.i("I2S deinitialized.")

        if self._playback_type == SoundPlayer._TYPE_WAV and self.wav:
            self.wav.close()
            self.wav = None
            Log.d("WAV file closed.")
        elif self._playback_type == SoundPlayer._TYPE_TONE:
            self._tone_buffer = None # Release tone buffer memory
            Log.d("Tone buffer released.")

        # Reset playback type and other relevant vars
        self._playback_type = SoundPlayer._TYPE_NONE
        self.loop = False
        self._tone_buffer_offset = 0
        self._tone_samples_played = 0
        self._tone_total_samples_to_play = 0
