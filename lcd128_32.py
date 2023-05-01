"""
Micropython (Raspberry Pi Pico)
2022/1/12     DENGFEI
lcd.Display() Only 94 limited characters in fonts can be displayed
"""

import machine
import time
import lcd128_32_fonts
cursor = [0, 0]
class lcd128_32:
    
    def __init__(self,dt,clk,bus,addr):
        self.addr = addr
        self.i2c = machine.I2C(bus,sda=machine.Pin(dt),scl=machine.Pin(clk))
        self.Init()
        
    def WriteByte_command(self, cmd):
        self.reg_write(0x00, cmd)
    
    def WriteByte_dat(self, dat):
        self.reg_write(0x40, dat)
    
    def reg_write(self, reg, data):
        msg = bytearray()
        msg.append(data)
        self.i2c.writeto_mem(self.addr, reg, msg)
    
    def Init(self):
        #self.i2c.start()
        time.sleep(0.01)
        self.WriteByte_command(0xe2)
        time.sleep(0.01)
        self.WriteByte_command(0xa3)
        self.WriteByte_command(0xa0)
        self.WriteByte_command(0xc8)
        self.WriteByte_command(0x22)
        self.WriteByte_command(0x81)
        self.WriteByte_command(0x30)
        self.WriteByte_command(0x2c)
        self.WriteByte_command(0x2e)
        self.WriteByte_command(0x2f)
        self.Clear()
        self.WriteByte_command(0xff)
        self.WriteByte_command(0x72)
        self.WriteByte_command(0xfe)
        self.WriteByte_command(0xd6)
        self.WriteByte_command(0x90)
        self.WriteByte_command(0x9d)
        self.WriteByte_command(0xaf)
        self.WriteByte_command(0x40)
    
    def Clear(self):
        for i in range(4):
            self.WriteByte_command(0xb0 + i)
            self.WriteByte_command(0x10)
            self.WriteByte_command(0x00)
            for j in range(128):
                self.WriteByte_dat(0x00)
    
    def Cursor(self, y, x):
        if x > 17:
            x = 17
        if y > 3:
            x = 3
        cursor[0] = y
        cursor[1] = x
        
    def WriteFont(self, num):
        for item in lcd128_32_fonts.textFont[num]:
            self.WriteByte_dat(item)
    
    def Display(self, str):
        self.WriteByte_command(0xb0 + cursor[0])
        self.WriteByte_command(0x10 + cursor[1] * 7 // 16)
        self.WriteByte_command(0x00 + cursor[1] * 7 % 16)
        for num in range(len(str)):
            if str[num] == '0':
                self.WriteFont(0)
            elif str[num] == '1':
                self.WriteFont(1)
            elif str[num] == '2':
                self.WriteFont(2)
            elif str[num] == '3':
                self.WriteFont(3)
            elif str[num] == '4':
                self.WriteFont(4)
            elif str[num] == '5':
                self.WriteFont(5)
            elif str[num] == '6':
                self.WriteFont(6)
            elif str[num] == '7':
                self.WriteFont(7)
            elif str[num] == '8':
                self.WriteFont(8)
            elif str[num] == '9':
                self.WriteFont(9)
            elif str[num] == 'a':
                self.WriteFont(10)
            elif str[num] == 'b':
                self.WriteFont(11)
            elif str[num] == 'c':
                self.WriteFont(12)
            elif str[num] == 'd':
                self.WriteFont(13)
            elif str[num] == 'e':
                self.WriteFont(14)
            elif str[num] == 'f':
                self.WriteFont(15)
            elif str[num] == 'g':
                self.WriteFont(16)
            elif str[num] == 'h':
                self.WriteFont(17)
            elif str[num] == 'i':
                self.WriteFont(18)
            elif str[num] == 'j':
                self.WriteFont(19)
            elif str[num] == 'k':
                self.WriteFont(20)
            elif str[num] == 'l':
                self.WriteFont(21)
            elif str[num] == 'm':
                self.WriteFont(22)
            elif str[num] == 'n':
                self.WriteFont(23)
            elif str[num] == 'o':
                self.WriteFont(24)
            elif str[num] == 'p':
                self.WriteFont(25)
            elif str[num] == 'q':
                self.WriteFont(26)
            elif str[num] == 'r':
                self.WriteFont(27)
            elif str[num] == 's':
                self.WriteFont(28)
            elif str[num] == 't':
                self.WriteFont(29)
            elif str[num] == 'u':
                self.WriteFont(30)
            elif str[num] == 'v':
                self.WriteFont(31)
            elif str[num] == 'w':
                self.WriteFont(32)
            elif str[num] == 'x':
                self.WriteFont(33)
            elif str[num] == 'y':
                self.WriteFont(34)
            elif str[num] == 'z':
                self.WriteFont(35)
            elif str[num] == 'A':
                self.WriteFont(36)
            elif str[num] == 'B':
                self.WriteFont(37)
            elif str[num] == 'C':
                self.WriteFont(38)
            elif str[num] == 'D':
                self.WriteFont(39)
            elif str[num] == 'E':
                self.WriteFont(40)
            elif str[num] == 'F':
                self.WriteFont(41)
            elif str[num] == 'G':
                self.WriteFont(42)
            elif str[num] == 'H':
                self.WriteFont(43)
            elif str[num] == 'I':
                self.WriteFont(44)
            elif str[num] == 'J':
                self.WriteFont(45)
            elif str[num] == 'K':
                self.WriteFont(46)
            elif str[num] == 'L':
                self.WriteFont(47)
            elif str[num] == 'M':
                self.WriteFont(48)
            elif str[num] == 'N':
                self.WriteFont(49)
            elif str[num] == 'O':
                self.WriteFont(50)
            elif str[num] == 'P':
                self.WriteFont(51)
            elif str[num] == 'Q':
                self.WriteFont(52)
            elif str[num] == 'R':
                self.WriteFont(53)
            elif str[num] == 'S':
                self.WriteFont(54)
            elif str[num] == 'T':
                self.WriteFont(55)
            elif str[num] == 'U':
                self.WriteFont(56)
            elif str[num] == 'V':
                self.WriteFont(57)
            elif str[num] == 'W':
                self.WriteFont(58)
            elif str[num] == 'X':
                self.WriteFont(59)
            elif str[num] == 'Y':
                self.WriteFont(60)
            elif str[num] == 'Z':
                self.WriteFont(61)
            elif str[num] == '!':
                self.WriteFont(62)
            elif str[num] == '"':
                self.WriteFont(63)
            elif str[num] == '#':
                self.WriteFont(64)
            elif str[num] == '$':
                self.WriteFont(65)
            elif str[num] == '%':
                self.WriteFont(66)
            elif str[num] == '&':
                self.WriteFont(67)
            elif str[num] == '\'':
                self.WriteFont(68)
            elif str[num] == '(':
                self.WriteFont(69)
            elif str[num] == ')':
                self.WriteFont(70)
            elif str[num] == '*':
                self.WriteFont(71)
            elif str[num] == '+':
                self.WriteFont(72)
            elif str[num] == ',':
                self.WriteFont(73)
            elif str[num] == '-':
                self.WriteFont(74)
            elif str[num] == '/':
                self.WriteFont(75)
            elif str[num] == ':':
                self.WriteFont(76)
            elif str[num] == ';':
                self.WriteFont(77)
            elif str[num] == '<':
                self.WriteFont(78)
            elif str[num] == '=':
                self.WriteFont(79)
            elif str[num] == '>':
                self.WriteFont(80)
            elif str[num] == '?':
                self.WriteFont(81)
            elif str[num] == '@':
                self.WriteFont(82)
            elif str[num] == '{':
                self.WriteFont(83)
            elif str[num] == '|':
                self.WriteFont(84)
            elif str[num] == '}':
                self.WriteFont(85)
            elif str[num] == '~':
                self.WriteFont(86)
            elif str[num] == ' ':
                self.WriteFont(87)
            elif str[num] == '.':
                self.WriteFont(88)
            elif str[num] == '^':
                self.WriteFont(89)
            elif str[num] == '_':
                self.WriteFont(90)
            elif str[num] == '`':
                self.WriteFont(91)
            elif str[num] == '[':
                self.WriteFont(92)
            elif str[num] == '\\':
                self.WriteFont(93)
            elif str[num] == ']':
                self.WriteFont(94)
