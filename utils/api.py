import json
import os
from homeassistant_api import Client , WebsocketClient
import re
import time
import yaml

def makeData(on, off, trans):
    """
    某些灯的开启关闭与渐变时间不是单独的变量
    而是使用一个四字节的整形变量来表示
    其中几个字节分别为 开启时间，关闭时间，渐变时间，标志位
    使用set_numers修改时需要生成目标值并一次性设置此三项值
    """
    assert on <= 30000 and on >= 100
    assert off <= 30000 and off >= 100
    assert trans <= 30000 and trans >= 100
    onVal = on // 100 if on <= 900 else 0x40 + on // 1000
    offVal = off // 100 if off <= 900 else 0x40 + off // 1000
    transVal = trans // 100 if trans <= 900 else 0x40 + trans // 1000
    flag = 0x01
    return flag << 24 | (transVal << 16) | (offVal << 8) | onVal


class has:
    def __init__(self, url, token):
        self.client = Client(url, token)
        # self.client = WebsocketClient(url, token)

    def select_entrys(self , domain, regex_list):
        '''使用正则表达式选择实体
        domain: 实体域
        regex_list: 正则表达式列表
        return: 匹配的实体列表
        '''
        result = []
        entities = self.client.get_entities()[domain]
        for entityID in entities.entities:
            if any(re.match(regex, entities.entities[entityID].state.attributes["friendly_name"]) != None for regex in regex_list):
                result.append(entities.entities[entityID])
        return result

    def set_lights(self , regex_list, brightness=None, kelvin=None, dry_run=True):
        '''设置灯光
        regex_list: 正则表达式列表，使用friendly_name匹配实灯光体
        brightness: 亮度，范围0-100
        kelvin: 色温，范围2700-6500
        dry_run: 是否测试运行
        return: None
        '''
        light_domain = self.client.get_domain("light")
        for entity in self.select_entrys("light", regex_list):
            print(f"亮度={brightness}% 色温={kelvin}k :\t[{entity.state.attributes['friendly_name']}]")
            if not dry_run:
                start = time.perf_counter_ns()
                if brightness is None and kelvin is None:
                    light_domain.turn_on(entity.state.entity_id)
                elif brightness is not None and kelvin is None:
                    light_domain.turn_on(entity.state.entity_id, brightness=int(brightness * 2.55))
                elif brightness is None and kelvin is not None:
                    light_domain.turn_on(entity.state.entity_id, kelvin=kelvin)
                else:
                    light_domain.turn_on(entity.state.entity_id, brightness=int(brightness * 2.55), kelvin=kelvin)
                end = time.perf_counter_ns()
                print(f"耗时={(end - start  )/ 1000000}ms")

    def set_numers(self , regex_list, value=None, dry_run=True):
        '''设置数值
        regex_list: 正则表达式列表，使用friendly_name匹配实体
        value: 数值
        dry_run: 是否测试运行
        return: None
        '''
        assert value is not None, "value is None"
        number_domain = self.client.get_domain("number")
        for entity in self.select_entrys("number", regex_list):
            print(f"数值={value} :\t[{entity.state.attributes['friendly_name']}]")
            if not dry_run:
                number_domain.set_value(entity.state.entity_id, value=value)

    def set_var(self , entity_id, value=None, dry_run=True):
        '''设置变量
        entity_id: 目标变量ID 
        value: 变量值
        dry_run: 是否测试运行
        return: None
        '''
        assert value is not None, "value is None"
        assert entity_id is not None, "entity_id is None"
        var_domain = self.client.get_domain("var")
        entity = self.client.get_entity("var", entity_id)
        if entity is not None:
            print(f"变量ID={entity_id} :\t[{entity.state.attributes['friendly_name']}] , 变量值={value}")
            if not dry_run:
                var_domain.set(entity.state.entity_id, value=value)
    
    
    # def generate_light_brightness_kevlin_var_map_yaml(self , regx_list  ):
    #     mapped_variables = {}
    #     for entity in  self.select_entrys("light", regx_list):
    #         entity_id = entity.state.entity_id
    #         assert entity_id.startswith("light.")
    #         print(f"实体ID: {entity_id}")
    #         # print(f"友好名称: {entity.state.attributes['friendly_name']}")
    #         mapped_variables[f"light_brightness_{entity_id[6:]}"] = {
    #             "friendly_name":f'{ entity.state.attributes["friendly_name"]} 目标亮度',
    #             "initial_value": 80,
    #             "restore": False,
    #             "icon": "mdi:brightness-6"
    #         }
    #         mapped_variables[f"light_kelvin_{entity_id[6:]}"] = {
    #             "friendly_name": f'{ entity.state.attributes["friendly_name"]} 目标色温 ',
    #             "initial_value": 4700,
    #             "restore": False,
    #             "icon": "mdi:temperature-kelvin"
    #         }
    #     return yaml.dump(mapped_variables, allow_unicode=True, default_flow_style=False, sort_keys=False)



# #=============EXAMPLE=========================

# # 打开并设置书房灯光
# hs.set_lights(lights_map["书房"], brightness=100, kelvin=4700, dry_run=True)

# # 设置电脑桌灯带的 渐变时长
# hs.set_numers([r"^电脑桌灯带.*((开|关)灯渐变时长|灯光调光时长).+$" ] , 3000 , dry_run = True)

# # 设置厨房灯的 渐变时长
# hs.set_numers([r"^厨房灯.*默认状态 渐变时间设置.+$" ] , makeData(2000, 4000, 3000) , dry_run = True)

# # 设置电脑桌灯带的目标亮度与目标色温
# entrys = hs.select_entrys("light", [r"^.*电脑桌灯带.*$"])
# assert len(entrys) == 1
# target_light_entry_id = entrys[0].state.entity_id
# hs.set_var(f"light_brightness_{target_light_entry_id[6:]}",10, dry_run=False)
# # # time.sleep(1)
# hs.set_var(f"light_kelvin_{target_light_entry_id[6:]}",3000 , dry_run=False)

# # 创建灯光目标值变量映射
# res = hs.generate_light_brightness_kevlin_var_map_yaml([ element for sublist in lights_map.values() for element in sublist])
# print(res)


