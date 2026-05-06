import os
import itertools
import random
import re
import pandas as pd
import openpyxl
import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from tinytroupe.examples import *
from openai import OpenAI


price_levels = ["low", "medium", "high"]
brand_levels = ["low", "medium", "high"]
quality_levels = ["low", "medium", "high"]

combinations = list(itertools.product(
    price_levels,
    brand_levels,
    quality_levels
))
selected_combinations = random.sample(combinations, 10)

def create_agent(idx, price, brand, quality):
    agent = TinyPerson(name=f"agent_{idx}")
    
    agent.define("price_sensitivity", price)
    agent.define("brand_preference", brand)
    agent.define("quality_preference", quality)
    
    return agent

def add_demographics(agent):
    agent.define("income_level", random.choice(["low", "medium", "high"]))

def build_prompt(strategy):
    return f"""
你正在考慮是否購買一個智能水瓶。

廣告：
{strategy["description"]}

請根據這個廣告和你的偏好、收入(income_level)評估你的購買意願。

請輸出(不要使用簡體字)：
評分: 0-10（整數，以5~6分為偏向購買/不買的分界線）
原因: 一句話
"""
def extract_score(text):
    match = re.search(r"評分[:：]\s*(\d+)", text)
    return int(match.group(1)) if match else None

def parse_response(text):
    
    score_match = re.search(r"評分[:：]\s*(\d+)", text)
    reason_match = re.search(r"原因[:：是]\s*(.*)", text)

    score = int(score_match.group(1)) if score_match else None
    reason = reason_match.group(1).strip() if reason_match else ""

    return score, reason

def get_attr(agent, key):
    persona=agent._persona
    return persona[key]

def get_last_talk(agent):
    # 嘗試不同可能的屬性名稱
    memory_sources = []

    if hasattr(agent, "memory"):
        memory_sources.append(agent.memory)
    if hasattr(agent, "trace"):
        memory_sources.append(agent.trace)
    if hasattr(agent, "events"):
        memory_sources.append(agent.events)

    # 找最後一個 TALK
    for memory in memory_sources:
        try:
            for item in reversed(memory):
                # 常見格式1: dict
                if isinstance(item, dict):
                    if item.get("type") == "TALK":
                        return item.get("content", "")
                
                # 常見格式2: object
                if hasattr(item, "type") and item.type == "TALK":
                    return getattr(item, "content", "")
        except:
            continue

    return ""

agents = []
for i, (p, b, q) in enumerate(selected_combinations):
    agent = create_agent(i, p, b, q)
    add_demographics(agent)
    agents.append(agent)

world = TinyWorld("marketing_simulation", agents)

strategies = [
    {
        "name": "折扣促銷",
        "description": "限時7折開搶！智能水瓶幫你精準記錄飲水量，健康升級不必花大錢。現在入手最划算，錯過再等一年！"
    },
    {
        "name": "高端品牌",
        "description": "為追求品質生活的你而生，智能水瓶結合極簡設計與精準科技，全天候守護你的健康，展現不凡品味。"
    },
    {
        "name": "社群推薦",
        "description": "超人氣網紅都在用！智能水瓶好評爆棚，輕鬆提醒喝水、養成好習慣，讓你每天都更有活力與自信。"
    },
    {
        "name": "訊息轟炸",
        "description": "限時7折熱賣中！這款智能水瓶結合高端設計與精準科技，不只外型質感出眾，更能貼心提醒補水、守護健康。眾多網紅與用戶一致好評推薦，輕鬆養成每日喝水好習慣。現在入手最划算，用更聰明的方式升級你的生活品質！"
    },
]

startegy_not_used=[
    {
        "name": "高端品牌",
        "description": "為追求品質生活的你而生，智能水瓶結合極簡設計與精準科技，全天候守護你的健康，展現不凡品味。"
    },
    {
        "name": "社群推薦",
        "description": "超人氣網紅都在用！智能水瓶好評爆棚，輕鬆提醒喝水、養成好習慣，讓你每天都更有活力與自信。"
    },
    {
        "name": "訊息轟炸",
        "description": "超人氣網紅都在用！智能水瓶好評爆棚，輕鬆提醒喝水、養成好習慣，讓你每天都更有活力與自信。"
    },
]
results = []
rows = []

for strategy in strategies:
    
    prompt = build_prompt(strategy)
    
    # 廣播給所有 agent
    world.broadcast(prompt)
    
    # 每個 agent 回應
    for agent in agents:
        response = agent.act(return_actions=True)
        results.append({
            "agent": agent.name,
            "strategy": strategy["name"],
        })
        
        print(agent.name+" "+strategy["name"])
        print(agent._persona)
        try:
            print(response[1]['action']['content'])
            score, reason = parse_response(response[1]['action']['content'])
        except:
            pass
        """
        episode=agent.episodic_memory.get_current_episode()
        try:
            print(episode[2]['content']['action']['content'])
            score, reason = parse_response(episode[2]['content']['action']['content'])
        except:
            pass
        """
        print("-" * 30)
        row = {
            "price_sensitivity": get_attr(agent, "price_sensitivity"),
            "brand_preference": get_attr(agent, "brand_preference"),
            "quality_preference": get_attr(agent, "quality_preference"),
            "income_level": get_attr(agent, "income_level"),
            "strategy": strategy["name"],
            "是否購買": "是" if int(score)>=6 else "否",
            "score": int(score),
            "reason": reason
        }

        rows.append(row)
        
    for agent in agents:
        agent.clear_episodic_memory()

df = pd.DataFrame(rows)
df.to_csv("simulation_results3.csv", index=False, encoding="utf-8-sig")
df.to_excel("simulation_results3.xlsx", index=False)
