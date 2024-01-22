# 登录 获取原始数据
import requests
import os
import ddddocr
import urllib.parse
from lxml import etree
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from binascii import a2b_hex, b2a_hex
from Crypto.Util.number import bytes_to_long
from info_parser import parse_student_info, parse_grades, calculate_gpa

class ZhengFangSpider:
    def __init__(self, student_id, password, student_name, base_url):
        self.grades = []
        self.is_logged_in = False
        self.grades_fetched = False
        self.student_id = student_id
        self.password = password
        self.student_name = student_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'

    #rsa加密密码部分
    @staticmethod
    def encrypt_with_modulus(content, public_exponent, modulus=None):
        e = int(public_exponent, 16)  # 指数
        n = bytes_to_long(a2b_hex(modulus))
        rsa_key = RSA.construct((n, e))  # generate/export
        # public key
        public_key = rsa_key.publickey()
        cipher = PKCS1_v1_5.new(public_key)
        content = cipher.encrypt(content)
        content = b2a_hex(content)
        return str(content)
        pass

    # 含验证码登陆部分
    def login(self):
        loginurl = self.base_url + "/default2.aspx"
        response = self.session.get(loginurl)
        selector = etree.HTML(response.content)
        # 获取验证码的参数
        safe_key = selector.xpath('//*[@id="icode"]/@src')[0].split('=')[1]
        # 获取公钥参数
        txtKeyExponent = selector.xpath('//*[@id="txtKeyExponent"]/@value')[0]
        txtKeyModulus = selector.xpath('//*[@id="txtKeyModulus"]/@value')[0]
        # 加密密码
        encrypted_password = ZhengFangSpider.encrypt_with_modulus(
            self.password.encode('utf-8'),  # 将密码转换为字节
            txtKeyExponent,
            txtKeyModulus
        )
        cleaned_result = encrypted_password.replace("b'", "").rstrip("'")
        __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
        __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]
        
        imgUrl = self.base_url + "/CheckCode.aspx?SafeKey=" + safe_key
        imgresponse = self.session.get(imgUrl, stream=True)
        image = imgresponse.content
        DstDir = os.getcwd() + "\\"
        print("保存验证码到：" + DstDir + "code.jpg")
        try:
            with open(DstDir + "code.jpg", "wb") as jpg:
                jpg.write(image)
        except IOError:
            print("IO Error\n")
        finally:
            jpg.close()
        # 使用 ddddocr 来识别验证码
        ocr = ddddocr.DdddOcr()
        code = ocr.classification(image)
        print("识别验证码：" + code)
        RadioButtonList1 = u"学生".encode('gb2312', 'replace')
        data = {
            "__LASTFOCUS": "",
            "__VIEWSTATE": __VIEWSTATE,
            "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "txtUserName": self.student_id,
            "TextBox2": cleaned_result,
            "txtSecretCode": code,
            "RadioButtonList1": "学生",
            "Button1": "登录",
            "txtKeyExponent" : "010001",
            "txtKeyModulus": txtKeyModulus
        }
        # 登陆教务系统
        login_response = self.session.post(loginurl, data=data)
        if login_response.status_code == requests.codes.ok:
            self.is_logged_in = True
            print("登录成功")
            return True
        else:
            print("登录失败")
            self.is_logged_in = False
            return False
        pass


    # 获取学生信息部分
    def get_student_info(self):
        if not self.is_logged_in:
            if not self.login():
                print("登录失败，无法获取学生信息")
                return
        
        # 设置请求头
        info_url = f"{self.base_url}/xsgrxx.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121501"

        # 定义请求头
        headers = {
            "Host": "xk.jwc.zjsru.edu.cn",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": "http://xk.jwc.zjsru.edu.cn/xs_main.aspx?xh=202206314123",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        }

        # 发送GET请求时传入headers参数
        response = self.session.get(info_url, headers=headers)
        if response.status_code == requests.codes.ok:
            student_info = parse_student_info(response.text)
            self.student_info = student_info
        else:
            print("获取信息失败")
        pass


    # 获取学生成绩部分
    def get_student_grades(self):
        if not self.is_logged_in:
            if not self.login():
                print("登录失败，无法获取学生信息")
                return
        
        url = f"{self.base_url}/xscjcx.aspx?xh={self.student_id}&xm={urllib.parse.quote(self.student_name)}&gnmkdm=N121605"
        self.session.headers['Referer'] = self.base_url + "/xs_main.aspx?xh=" + self.student_id
        response = self.session.get(url)
        selector = etree.HTML(response.content)
        __VIEWSTATE = selector.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
        __VIEWSTATEGENERATOR = selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value')[0]

        # 提交获取成绩的POST请求
        data = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": __VIEWSTATE,
            "__VIEWSTATEGENERATOR" : __VIEWSTATEGENERATOR,
            "ddlXN": "",  # 可根据需要设置学年
            "ddlXQ": "",  # 可根据需要设置学期
            "ddl_kcxz": "",  # 可根据需要设置课程性质
            "btn_zcj": "历年成绩"
        }
        response = self.session.post(url, data=data, headers={"Referer": url})
        if response.status_code == requests.codes.ok:
            grades = parse_grades(response.text)
            self.grades = grades
            self.grades_fetched = True  # 成功获取成绩后，设置标志为 True
        else:
            print("获取学生成绩失败")




    def calculate_and_print_gpa(self):
        # 检查是否已获取成绩
        if not self.grades_fetched:
            print("还未获取成绩，正在尝试获取...")
            self.get_student_grades()
            if not self.grades_fetched:
                print("无法获取成绩，无法计算 GPA")
                return

        # 调用 calculate_gpa 函数计算 GPA
        term_gpa, year_gpa = calculate_gpa(self.grades)

        # 打印学期 GPA
        print("学期 GPA:")
        for term, data in term_gpa.items():
            print(f"{term} - GPA: {data['gpa']:.2f}, 总学分: {data['total_credits']}, 总绩点: {data['total_points']:.2f}")

        # 打印学年 GPA
        print("\n学年 GPA:")
        for year, data in year_gpa.items():
            print(f"{year} - GPA: {data['gpa']:.2f}, 总学分: {data['total_credits']}, 总绩点: {data['total_points']:.2f}")




