# 数据处理
import re
from lxml import etree
from bs4 import BeautifulSoup

# 解码输出学生信息部分        
def parse_student_info(html_content):
    selector = etree.HTML(html_content)
    student_info = {
        "学号": selector.xpath('//*[@id="xh"]/text()')[0],
        "姓名": selector.xpath('//span[@id="xm"]/text()')[0],
        "性别": selector.xpath('//span[@id="lbl_xb"]/text()')[0],
        "身份证号": selector.xpath('//span[@id="lbl_sfzh"]/text()')[0],
        "出生日期": selector.xpath('//span[@id="lbl_csrq"]/text()')[0],
        "入学日期": selector.xpath('//span[@id="lbl_rxrq"]/text()')[0],
        "所在级": selector.xpath('//span[@id="lbl_dqszj"]/text()')[0],
        "所在学院": selector.xpath('//span[@id="lbl_xy"]/text()')[0],
        "所在专业": selector.xpath('//span[@id="lbl_zymc"]/text()')[0],
        "所在班级": selector.xpath('//span[@id="lbl_xzb"]/text()')[0],
        "民族": selector.xpath('//span[@id="lbl_mz"]/text()')[0],
        "籍贯": selector.xpath('//span[@id="lbl_jg"]/text()')[0],
        "政治面貌": selector.xpath('//span[@id="lbl_zzmm"]/text()')[0],
        "准考证号": selector.xpath('//span[@id="lbl_zkzh"]/text()')[0],
        "手机号码": selector.xpath('//span[@id="lbl_TELNUMBER"]/text()')[0],
        "学历": selector.xpath('//span[@id="lbl_CC"]/text()')[0],
    }
    return student_info
    pass



# 解码成绩部分
def parse_grades(html_content):
    soup = BeautifulSoup(html_content, "html5lib")
    trs = soup.find(id="Datagrid1").findAll("tr")[1:]
    grades = []
    for tr in trs:
        tds = tr.findAll("td")
        tds = tds[:2] + tds[3:5] + tds[6:9]
        oneGradeKeys = ["year", "term", "name", "type", "credit", "gradePoint", "grade"]
        oneGradeValues = [td.string for td in tds]
        oneGrade = dict(zip(oneGradeKeys, oneGradeValues))
        grades.append(oneGrade)
    return grades


# 计算gpa部分
def calculate_gpa(grades):
    term_gpa = {}
    year_gpa = {}

    for grade in grades:
        year = grade['year']
        term = grade['term']
        credit = float(grade['credit'])
        grade_point = float(grade['gradePoint'].strip())

        # 学年数据
        if year not in year_gpa:
            year_gpa[year] = {'total_points': 0, 'total_credits': 0}
        year_gpa[year]['total_points'] += credit * grade_point
        year_gpa[year]['total_credits'] += credit

        # 学期数据
        term_key = f"{year} {term}"
        if term_key not in term_gpa:
            term_gpa[term_key] = {'total_points': 0, 'total_credits': 0}
        term_gpa[term_key]['total_points'] += credit * grade_point
        term_gpa[term_key]['total_credits'] += credit

    # 计算每个学期和学年的GPA
    for key, value in term_gpa.items():
        gpa = value['total_points'] / value['total_credits'] if value['total_credits'] > 0 else 0
        term_gpa[key]['gpa'] = gpa

    for key, value in year_gpa.items():
        gpa = value['total_points'] / value['total_credits'] if value['total_credits'] > 0 else 0
        year_gpa[key]['gpa'] = gpa

    return term_gpa, year_gpa


# 获取__VIEWSTATE和__VIEWSTATEGENERATOR的值
def get_viewstate_values(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 查找__VIEWSTATE和__VIEWSTATEGENERATOR的元素
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']

    return viewstate, viewstate_generator


# 解码课表部分
def parse_class_schedule(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    day_mapping = {
        '一': 'Monday',
        '二': 'Tuesday',
        '三': 'Wednesday',
        '四': 'Thursday',
        '五': 'Friday',
        '六': 'Saturday',
        '日': 'Sunday'
    }


    schedule = {
        'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [],
        'Friday': [], 'Saturday': [], 'Sunday': []
    }


    course_entries = soup.find_all('td', align="center")

    for entry in course_entries:
        rowspan = int(entry.get('rowspan', 1))  
        details = [detail.strip() for detail in entry.stripped_strings if detail.strip()]
        
        if len(details) >= 4:  
            course_name = details[0]
            day_period_week = details[1]  
            day_of_week_str = day_period_week[1]  
            day_of_week = day_mapping.get(day_of_week_str, 'Unknown')
            period = day_period_week.split('第')[1].split('节')[0]  
            week = day_period_week[day_period_week.find("{")+1:day_period_week.find("}")]  
            teacher = details[2]
            location = details[3] if len(details) > 3 else '未知'
            time = details[4] if len(details) > 4 else ''

            for period_idx in range(rowspan):
                if rowspan > 1:
                    period_details = f"{period.split(',')[0]}-{int(period.split(',')[0])+period_idx}"
                    course_info = f"{course_name} 周{day_of_week_str}第{period_details}节{week} {teacher} {location} {time}"
                else:
                    course_info = f"{course_name} 周{day_of_week_str}第{period}节{week} {teacher} {location} {time}"
                schedule[day_of_week].append(course_info)

    # Format the schedule for output
    formatted_schedule = ""
    for day, courses in schedule.items():
        if courses:  
            formatted_schedule += f"{day}:\n" + "\n".join(courses) + "\n\n"
    return formatted_schedule.strip()
