import re
from config import MAX_CHARACTOR_SIZE

class SplitSentence(object):
    """ 分句，将文本切分为若干句子，其中处理引号的部分逻辑情况较多

    Args:
        text(str): 字符串文本
        criterion(coarse/fine): 句子切分粒度，粗细两种 `coarse` 或 `fine`，
            `coarse` 指的是按句号级别切分，`fine` 指按所有标点符合切分，
            默认按照粗粒度进行切分

    Returns:
        list(str): 分句后的句子列表

    Examples:
        >>> text = '中华古汉语，泱泱大国，历史传承的瑰宝。'
        >>> print(jio.split_sentence(text, criterion='fine'))

        # ['中华古汉语，', '泱泱大国，', '历史传承的瑰宝。']

    """
    def __init__(self):
        self.puncs_fine = None
        
    def _prepare(self):
        self.puncs_fine = {'……', '\r\n', '，', '。', ';', '；', '…', '！', '!',
                           '?', '？', '\r', '\n', '“', '”', '‘', '’', '：'}
        self.puncs_coarse = {'。', '！', '？', '\n', '“', '”', '‘', '’'}
        self.front_quote_list = {'“', '‘'}
        self.back_quote_list = {'”', '’'}

        self.puncs_coarse_ptn = re.compile('([。“”！？\n])')
        self.puncs_fine_ptn = re.compile('([，：。;“”；…！!?？\r\n])')
        
    def __call__(self, text, criterion='coarse'):

        if self.puncs_fine is None:
            self._prepare()

        if criterion == 'coarse':
            tmp_list = self.puncs_coarse_ptn.split(text)
        elif criterion == 'fine':
            tmp_list = self.puncs_fine_ptn.split(text)
        else:
            raise ValueError('The parameter `criterion` must be '
                             '`coarse` or `fine`.')
        
        final_sentences = []
        quote_flag = False
        
        for sen in tmp_list:
            if sen == '':
                continue

            if criterion == 'coarse':
                if sen in self.puncs_coarse:
                    if len(final_sentences) == 0:  # 即文本起始字符是标点
                        if sen in self.front_quote_list:  # 起始字符是前引号
                            quote_flag = True
                        final_sentences.append(sen)
                        continue
                    
                    # 以下确保当前标点前必然有文本且非空字符串
                    # 前引号较为特殊，其后的一句需要与前引号合并，而不与其前一句合并
                    if sen in self.front_quote_list:
                        if final_sentences[-1][-1] in self.puncs_coarse:
                            # 前引号前有标点如句号，引号等：另起一句，与此合并
                            final_sentences.append(sen)
                        else:
                            # 前引号之前无任何终止标点，与前一句合并
                            final_sentences[-1] = final_sentences[-1] + sen
                        quote_flag = True
                    else:  # 普通,非前引号，则与前一句合并
                        final_sentences[-1] = final_sentences[-1] + sen
                    continue
                    
            elif criterion == 'fine':
                if sen in self.puncs_fine:
                    if len(final_sentences) == 0:  # 即文本起始字符是标点
                        if sen in self.front_quote_list:  # 起始字符是前引号
                            quote_flag = True
                        final_sentences.append(sen)
                        continue
                    
                    # 以下确保当前标点前必然有文本且非空字符串
                    # 前引号较为特殊，其后的一句需要与前引号合并，而不与其前一句合并
                    if sen in self.front_quote_list:
                        if final_sentences[-1][-1] in self.puncs_fine:
                            # 前引号前有标点如句号，引号等：另起一句，与此合并
                            final_sentences.append(sen)
                        else:
                            # 前引号之前无任何终止标点，与前一句合并
                            final_sentences[-1] = final_sentences[-1] + sen
                        quote_flag = True
                    else:  # 普通,非前引号，则与前一句合并
                        final_sentences[-1] = final_sentences[-1] + sen
                    continue
            
            if len(final_sentences) == 0:  # 起始句且非标点
                final_sentences.append(sen)
                continue
                
            if quote_flag:  # 当前句子之前有前引号，须与前引号合并
                final_sentences[-1] = final_sentences[-1] + sen
                quote_flag = False
            else:
                if final_sentences[-1][-1] in self.back_quote_list:
                    # 此句之前是后引号，需要考察有无其他终止符，用来判断是否和前句合并
                    if len(final_sentences[-1]) <= 1:
                        # 前句仅一个字符。后引号，则合并
                        final_sentences[-1] = final_sentences[-1] + sen
                    else:  # 前句有多个字符，
                        if criterion == 'fine':
                            if final_sentences[-1][-2] in self.puncs_fine:
                                # 有逗号等，则需要另起一句，该判断不合语文规范，但须考虑此情况
                                final_sentences.append(sen)
                            else:  # 前句无句号，则需要与前句合并
                                final_sentences[-1] = final_sentences[-1] + sen
                            
                        elif criterion == 'coarse':
                            if final_sentences[-1][-2] in self.puncs_coarse:
                                # 有句号，则需要另起一句
                                final_sentences.append(sen)
                            else:  # 前句无句号，则需要与前句合并
                                final_sentences[-1] = final_sentences[-1] + sen
                else:
                    final_sentences.append(sen)
                
        return final_sentences
    

def get_redundant_pattern():
    pattern_list = list()
    redundant_pattern_str = ' -\t\n啊哈呀嗯~\u3000\xa0•·・ #@！!*'
    for char in redundant_pattern_str:
        pattern_tmp = '(?<={char}){char}+'.format(
            char=re.escape(char))
        pattern_list.append(pattern_tmp)

    redundant_pattern = '|'.join(pattern_list)
    redundant_pattern = re.compile(redundant_pattern)
    return redundant_pattern

REDUNDANT_PATTERN = get_redundant_pattern()

def clean_text(text):
    text = REDUNDANT_PATTERN.sub('', text)
    cleaned_text = re.sub(r"\s+", " ", text.strip())
    cleaned_text = re.sub('\n+','\n',cleaned_text)
    return cleaned_text



sent_split = SplitSentence()

def split_sents_chunks(sents, chunk_size=500):
    chunks = []
    tmp = []
    tmp_size = 0
    for s in sents:
        if len(s) + tmp_size >= chunk_size:
            if tmp:
                chunks.append(tmp)
                tmp = []
                tmp_size = 0
            else:
                chunks.append([s])
        else:
            tmp.append(s)
            tmp_size += len(s)
    if tmp:
        chunks.append(tmp)
    return chunks

def split_doc_content_to_chunks(doc):
    content = doc['content']
    content = REDUNDANT_PATTERN.sub('', content)[:MAX_CHARACTOR_SIZE]
    sents = sent_split(content)
    chunks = split_sents_chunks(sents)
    return chunks
