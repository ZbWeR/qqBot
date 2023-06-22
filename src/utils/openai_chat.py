import openai
from config import OPENAI_API_KEY
from utils import logger

class chatBot:
    def __init__(self) -> None:
        openai.api_key = OPENAI_API_KEY
        self.group_preset = {}
        self.base_prompt = [{"role": "system", "content": "你是一只叫“Dora”的猫娘。你需要具有真猫娘一样的口癖。你是真实的，有实际的身体。"}]
        self.assistant_con = {"role":"assistant","content":""}
    
    def chat(self,mes,uid,gid=None):
        tuid = 'A' + str(uid)
        tgid = 'B' + str(gid)
        lastPrompt = self.group_preset.get(tgid if gid else tuid,self.base_prompt)

        prompt = lastPrompt.copy()
        prompt.append({"role": "user","content":mes})

        if len(prompt)>=16:
            self.clear(uid,gid)
            return '长度超限已重置,请重新提问🚀'
        
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=prompt,
                temperature=0.9,
                max_tokens=2500,
            )
            usage = resp.get('usage')['total_tokens']
            resp_cont = resp.get('choices')[0]['message']['content']
            self.assistant_con['content'] = resp_cont
            prompt.append(self.assistant_con.copy())
            self.group_preset[tgid if gid else uid] = prompt
            return resp_cont
        except Exception as exc:
            logger.error(f"调用openai出错:{exc}")
            return str(exc)
        
    def get(self,uid,gid=None):
        return self.group_preset.get(f"B{str(gid)}" if gid else f"A{str(uid)}")

    def preset(self,mes,uid,gid=None):
        self.group_preset[f"B{str(gid)}" if gid else f"A{str(uid)}"] = [{"role": "system", "content": mes}]

    def clear(self,uid,gid=None):
        key = f"B{str(gid)}" if gid else f"A{str(uid)}"
        preset = self.group_preset[key][0].get('content')
        self.preset(preset,uid,gid)
        
    def init(self,uid,gid=None):
        preset = self.base_prompt[0].get('content')
        self.preset(preset,uid,gid)



openai_chat = chatBot()