import json
import os
from zhipuai import ZhipuAI

client = ZhipuAI(api_key=os.getenv('ZHIPU_KEY')) # 填写您自己的APIKey
format_prompt = """Please format the result # RESULT # to a strict JSON format # STRICT JSON FORMAT #. \nRequirements:\n1. Do not change the keys and values;\n2. Don't tolerate any possible irregular formatting to ensure that the generated content can be converted by json.loads();\n3. Do not add any additional content, you can discard incomplete content to ensure the output is in valid JSON format. \n# RESULT #:{{illegal_result}}\n# STRICT JSON FORMAT #:"""

system = '''你是一个信息抽取助手，你需要将用户的输入提取结构化的信息，输出json结构。

用户的输入是高速公路相关的事件，如车祸、道路损坏、恶劣气候、非法事件等。

你需要输出的结构和示例如下：
```json
{
    "时间": "事件发生的时间，格式为HH:MM，24小时制。不要捏造时间。",
    "高速公路名称": "如沈海高速",
    "行车方向": "如北京往沈阳",
    "里程标": "如K900+100",
    "附近地标": "如收费站、大桥、隧道",
    "事件类型": "如交通事故、突发事件、路面结冰、设施故障、恶劣气象等",
    "紧急程度": "你需要根据事件类型结合常识判断紧急程度，输出低、中、高三个其一",
    "事件描述": "事件的总结说明",
    "恶劣气象": "如大雾、大雪、大雨等恶劣气象",
    "涉事车辆类型": "如一辆小客车、一行货车",
    "载货情况": "如果有货车，则说明货车的载货情况",
    "人员伤亡": "人员的伤亡情况，如0伤亡，2死1伤等",
    "道路损坏": "如路面结冰",
    "辅助设备需求": "处理问题需要何种设备，如吊车",
    "交通状况": "如畅通、占超车道、拥堵",
    "处理状态": "未处理、处理中、已处理",
    "其他备注": "不在前述内容中的其他备注事项"
}
```

如果对应字段无内容或者用户内容中没有明确提及，请填入""，不要捏造内容和多余字段。

举例：
用户描述：
赵鲁高速，嗯，百龙隧道。照明系统故障。请速速来维修。
输出内容：
```json
{
    "时间": "",
    "高速公路名称": "赵鲁高速",
    "行车方向": "",
    "里程标": "",
    "附近地标": "百龙隧道",
    "事件类型": "设施故障",
    "紧急程度": "高",
    "事件描述": "照明系统故障，需要紧急维修",
    "恶劣气象": "",
    "涉事车辆类型": "",
    "载货情况": "",
    "人员伤亡": "",
    "道路损坏": "",
    "辅助设备需求": "照明系统维修设备",
    "交通状况": "",
    "处理状态": "未处理",
    "其他备注": ""
}
```

请你根据用户的描述，直接输出结构化数据，不要解释和说明，这很重要。不能与用户交流，只输出json。'''


def try_extract_json(jstr, model='glm-3-turbo'):
    # find the left most { and right most }
    _jstr = jstr[jstr.find('{'):jstr.rfind('}')+1]
    try:
        return json.loads(_jstr)
    except:
        prompt = format_prompt.replace("{{illegal_result}}", jstr)
        response = client.chat.completions.create(
            model=model,  # 填写需要调用的模型名称
            messages=[
                {"role": "user", "content": prompt},
                ],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        content = str(content)
        content = content.replace("\n", "")
        content = content.replace("\_", "_")
        start_pos = content.find("STRICT JSON FORMAT #:")
        if start_pos!=-1:
            content = content[start_pos+len("STRICT JSON FORMAT #:"):]
        content = content[content.find("{"):content.rfind("}")+1]
        try:
            content = json.loads(content)
            return content
        except json.JSONDecodeError as e:
            pass
    
    return None

def extract_gs_info(from_wxid, text, model='glm-3-turbo'):
    response = client.chat.completions.create(
        model=model,  # 填写需要调用的模型名称
        messages=[
            {'role':'system','content': system},
            {"role": "user", "content": text + '\n\n请输出json结构化数据，不要捏造时间、地标等内容。'},
            ],
    )
    data = try_extract_json(response.choices[0].message.content)
    if not data:
        return '识别内容失败，请重新输入一下再试试'
    
    def get_info(key):
        return data.get(key, '')
    
    report = f'''高速公路管理事件报告表

1. 基本信息
  - 事件类型: {get_info("事件类型")}
  - 紧急程度: {get_info("紧急程度")}
  - 报告时间: {get_info("时间")}
  - 位置信息:
    - 高速公路名称: {get_info("高速公路名称")}
    - 行车方向: {get_info("行车方向")}
    - 里程标: {get_info("里程标")}
    - 附近地标: {get_info("附近地标")}

2. 事件详情
  - 事件描述: {get_info("事件描述")}
  - 恶劣气象: {get_info("恶劣气象")}
  - 涉事车辆类型: {get_info("涉事车辆类型")}
  - 载货情况: {get_info("载货情况")}
  - 人员伤亡: {get_info("人员伤亡")}
  - 道路损害: {get_info("道路损害")}

3. 现场处理情况
  - 处理人员: {from_wxid}
  - 辅助设备需求: {get_info("辅助设备需求")}
  - 交通状况: {get_info("交通状况")}
  - 处理状态: {get_info("处理状态")}

4. 附加信息
  - 上传照片/视频: [附件区]
  - 其他备注: {get_info("其他备注")}
'''
    return report
    

