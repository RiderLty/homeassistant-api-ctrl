from utils.api import has
from config.secrets import URL , TOKEN , LIGHTS_MAP
import os


hs = has(URL,TOKEN)
e = hs.select_entrys("light" , [ element for sublist in LIGHTS_MAP.values() for element in sublist ])

var_entries = ''
light_entries = ''
var_lights = ''
for entity in e:
    var_entries += f"      - {entity.state.entity_id.replace('light.' , 'var.light_brightness_')}\n"
    var_entries += f"      - {entity.state.entity_id.replace('light.' , 'var.light_kelvin_')}\n"
    light_entries += f"    - {entity.state.entity_id}\n"
    var_lights += f'''light_brightness_{entity.state.entity_id[6:]}:
  friendly_name: '{entity.state.attributes['friendly_name']}  目标亮度'
  initial_value: 80
  restore: false
  icon: mdi:brightness-6
light_kelvin_{entity.state.entity_id[6:]}:
  friendly_name: '{entity.state.attributes['friendly_name']}  目标色温'
  initial_value: 4700
  restore: false
  icon: mdi:temperature-kelvin
'''

var_control_lights = r'''alias: 目标值变化时调整已开启的灯光
description: ""
triggers:
  - trigger: state
    entity_id:
      - var.replacelist
    from: null
    to: null
conditions:
  - condition: template
    value_template: >-
      {% set mapped_entity = trigger.entity_id |
      regex_replace('^var\.light_(brightness|kelvin)_', 'light.')  %}
      {{states(mapped_entity) == 'on' }}
actions:
  - if:
      - condition: template
        value_template: "{{trigger.entity_id.startswith('var.light_brightness_')}}"
    then:
      - action: light.turn_on
        metadata: {}
        data:
          brightness_pct: |-
            {% set brightness_entity_id =
             trigger.entity_id|regex_replace('^var\.light_(brightness|kelvin)_','var.light_brightness_')
            %} {{states(brightness_entity_id)|int}}
        target:
          entity_id: >-
            {% set mapped_entity_id =
            trigger.entity_id|regex_replace('^var\.light_(brightness|kelvin)_','light.')
            %} {{mapped_entity_id}}
    else:
      - action: light.turn_on
        metadata: {}
        data:
          color_temp_kelvin: |-
            {% set brightness_entity_id =
              trigger.entity_id|regex_replace('^var\.light_(brightness|kelvin)_','var.light_kelvin_')
             %} {{states(brightness_entity_id)|int}}
        target:
          entity_id: >-
            {% set mapped_entity_id =
            trigger.entity_id|regex_replace('^var\.light_(brightness|kelvin)_','light.')
            %} {{mapped_entity_id}}
mode: parallel
'''

set_lights_to_var_target = r'''alias: 开启灯光时调整到变量设定的目标值
description: ""
triggers:
  - entity_id:
    - light.replacelist
    trigger: state
    from: "off"
    to: "on"
conditions: []
actions:
  - action: light.turn_on
    target:
      entity_id: "{{ trigger.entity_id }}"
    data:
      color_temp_kelvin: "{{ states('var.light_kelvin_' ~ trigger.entity_id[6:]) | int }}"
      brightness_pct: "{{ states('var.light_brightness_' ~ trigger.entity_id[6:]) | int }}"
mode: parallel
'''

var_control_lights = var_control_lights.replace("      - var.replacelist" , var_entries)
set_lights_to_var_target = set_lights_to_var_target.replace("    - light.replacelist" , light_entries)

os.makedirs("yaml" , exist_ok=True)
with open("yaml/var_control_lights.yaml" , "w" , encoding="utf-8") as f:
    f.write(var_control_lights)
with open("yaml/set_lights_to_var_target.yaml" , "w" , encoding="utf-8") as f:
    f.write(set_lights_to_var_target)
with open("yaml/var_lights.yaml" , "w" , encoding="utf-8") as f:
    f.write(var_lights) 
