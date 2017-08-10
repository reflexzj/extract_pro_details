# coding=utf-8
from choose_data import optimization

def get_entitys(row_ch):
    '''
    统计中文字符串中，对应实体的种类（ch.txt文件中给出了sentences中每行包含的实体名）
    :param row_ch: ch.txt中对应行的所有实体名（通过斯坦福coreNLP中文模型工具，逐行分析，结果存入ch.txt文件中去）
    :return: 返回对应行，实体种类
    '''
    entitys = []
    ch_alls = row_ch.strip().split(' ')

    for entity in ch_alls:
        if entity not in entitys and entity:
            entitys.append(entity)

    return entitys


def judge_absent(row_content, category):
    '''
    判断缺省某个实体后，需要满足的额外条件
    :param row_content: sentences中对应的行（文本）
    :param category: 额外规则种类（对应txt文本匹配词）
    :return:
    '''
    rex = open('../data/rule/'+category+'/absent.txt', 'r')

    for token in rex:
        token = token.strip('\n').strip(' ')
        if token and token in row_content:
            return True

    return False

def judge_all(row_content, category , mode = 'all', MIN_LEN = 20):
    '''
    对文本应该先进行先验判断，某些词至少含有一个，或者某些词一次都不能出现
    :param row_content:
    :param category:
    :param mode: 3种模式:contain,no_contain,all
    :return:
    '''

    if len(row_content)< MIN_LEN:
        return False


    contain, not_contain = 0 , 1

    rex_c = open('../data/rule/'+category+'/contain.txt', 'r')
    rex_n = open('../data/rule/'+category+'/notC.txt', 'r')

    for token in rex_c:
        token = token.strip('\n').strip(' ')
        if token and token in row_content:
            contain  = 1
            break

    for token in rex_n:
        token = token.strip('\n').strip(' ')
        if token and token in row_content:
            not_contain = 0
            break

    if mode == 'contain':
        return contain
    if mode == 'not_contain':
        return not_contain
    if mode == 'all':
        return contain and not_contain

def judge_in(entitys, sub_rule, mode = 'or'):
    '''
    判断子规则中是否包含某个实体，两种模式：全包含，至少包含一个
    :param entitys:
    :param sub_rule: 一个list，子规则（实体名的集合）
    :param mode: or,all
    :return:
    '''

    if mode == 'or':
        for entity in entitys:
            if entity in sub_rule :
                return True
        return False

    elif mode == 'all':
        for entity in sub_rule:
            if entity not in entitys:
                return False
        return True



def match_rule(row_content, rules, entitys, category, mode, MIN_LEN):
    '''
    判断当前的句子符不符合规则，返回boolean值
    :param rules: 规则包含四种子规则（针对实体的覆盖情况），可以缺省,有缺省判断（_sel）,不包含（_no）,全包含（_and）,选择包含（_or）
    :param entitys: 实体集合
    :param count:
    :return:
    '''

    # 先验判断
    if  not judge_all(row_content, category, mode, MIN_LEN):
        return False

    # 实体规则判断
    for key in rules.keys():
        if key == '_no':
            if judge_in(entitys, rules[key]):
                return False

        elif key == '_sel':
            if judge_in(entitys, rules[key]):
                if not judge_absent(row_content, category):
                    return False
            else:
                return False

        elif key == '_or':
            if not judge_in(entitys, rules[key]):
                return False

        elif key == '_and':
            if not judge_in(entitys, rules[key], 'all'):
                return False

    return True




def give_sentences(rule, category, mode, fp, MIN_LEN):
    """
    返回满足规则的句子，写到fp文件中去
    :param rule: 给定的规则
    :param category: 规则种类
    :param mode: 选择先验模式
    :param fp:
    :return:
    """
    ch = open('../data/entities/ch.txt', 'r')
    ch_lines = ch.readlines()

    result = open('../data/sentences/sentences.txt', 'r')
    result_lines = result.readlines()

    tags = open('../data/sentences/tags.txt', 'r')
    tags_lines = tags.readlines()

    lines = []
    rows = len(ch_lines)


    # 逐行读取，将满足规则句子所在行号记录下来（entitys[0]记录的就是行号，从1开始）
    for i in range(rows):
        entitys = get_entitys(ch_lines[i])
        row_content = optimization(result_lines[i].strip('\n'))

        if match_rule(row_content, rule, entitys, category, mode, MIN_LEN):
            lines.append(int(entitys[0]))


    # 将对应条目写到一行里面
    flag = ''
    for line in lines:
        data = optimization(result_lines[line - 1].strip('\n'))
        # print line, ':' , data
        tag = tags_lines[line - 1].split(' ')
        name = tag[0]
        college = tag[1]
        company = tag[2].strip('\n')

        if flag == name:
            fp.write( data.strip('\n') + '。')
        else:
            flag = name
            fp.write('\n'+ flag+ ','+ college+','+ company+ ',')
            fp.write(data.strip('\n') + '。')

    return lines


def show_rows(lines):
    '''
    输出列表中行号的文本
    :param lines:
    :return:
    '''
    result = open('../data/sentences/sentences.txt', 'r')
    result_lines = result.readlines()

    for line in lines:
        row_data = result_lines[line-1].strip('\n')
        print line, ':', row_data


def find_miss(lines, batch):
    '''
    连着许多行都没有抽取到信息，需要观察
    :param lines:
    :param batch:
    :return:
    '''
    fp = open('../data/rule/find_miss.txt', 'w')
    length = len(lines)
    if length > 1:
        for i in range(1, length):
            if lines[i] - lines[i-1]> batch:
                fp.write(str(lines[i-1])+ ','+str(lines[i])+ '\n')



if __name__ == "__main__":

    career_csv = open('../data/final_result/career.csv', 'w')
    contribute_csv = open('../data/final_result/contribute.csv', 'w')
    job_csv = open('../data/final_result/job.csv', 'w')
    area_csv = open('../data/final_result/area.csv', 'w')


    career = {
                '_no': ['PERSON'],
                '_sel': ['DATE','TITLE'],
                '_or': ['ORGANIZATION','GPE','COUNTRY','STATE_OR_PROVINCE','FACILITY','LOCATION']
              }

    contribute = {
                    '_no': ['PERSON'],
                    '_or': ['ORGANIZATION','GPE','COUNTRY','STATE_OR_PROVINCE','FACILITY','LOCATION', 'ORDINAL', 'MISC']
                }

    job = {
            '_no': ['PERSON'],
            '_or': ['ORGANIZATION','GPE','COUNTRY','STATE_OR_PROVINCE','FACILITY','LOCATION']
            }

    area = {'O':[2,20]}


    l_car = give_sentences(career, 'career', 'not_contain', career_csv, 20)
    l_con = give_sentences(contribute, 'contribute', 'all', contribute_csv, 25)
    l_job = give_sentences(job, 'job', 'all', job_csv, 20 )
    # give_sentences(ch, area, area_csv)

    # 连着许多行都没有抽取到信息，需要观察
    # find_miss(l_job, 500)

    # 分析提取文本结果，完善规则表，显示冲突的抽取内容
    concflict = []

    for id in range(86910):
        if id in l_car and id in l_con and id in l_job:
            concflict.append(id)

    show_rows(concflict)













