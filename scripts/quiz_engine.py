#!/usr/bin/env python3
"""
poetry-quiz-engine.py  v4 — 追问模式 + AI友好JSON输出
核心设计：
  交互模式（默认）：生成当前题目 JSON → 退出
  AI 读取 JSON → 渲染为聊天界面（带选项按钮）
  用户点击选项 → AI 调用 --resume 验证并出下一题
  状态持久化在 /tmp/poetry-quiz-state.json
"""

import sys
import json
import random
import argparse
import os

STATE_FILE = "/tmp/poetry-quiz-state.json"

POEMS = {
    "咏鹅": {
        "author": "骆宾王（唐）",
        "text": ["鹅鹅鹅，曲项向天歌。", "白毛浮绿水，红掌拨清波。"],
        "mood": "宁静美好",
        "quiz_templates": [
            {"question": "白毛浮（      ），红掌拨清波。",
             "options": {"A": "绿水", "B": "蓝天", "C": "清水", "D": "大海"},
             "answer": "A", "tip": "白鹅浮在绿绿的水面上！",
             "hint": "提示：白鹅喜欢在绿绿的水里游泳~"},
            {"question": "鹅鹅鹅，曲项向（      ）。",
             "options": {"A": "天歌", "B": "地哭", "C": "水游", "D": "唱歌"},
             "answer": "A", "tip": "白鹅仰着头唱歌呢！",
             "hint": "提示：天鹅会仰着头唱歌哦~"},
            {"question": "白鹅的脚掌是什么颜色的？",
             "options": {"A": "红色", "B": "黑色", "C": "白色", "D": "橙色"},
             "answer": "A", "tip": "红红的脚掌拨动清清的水~",
             "hint": "提示：看看白鹅的图片，它的脚是红红的~"},
            {"question": "白鹅在水里干什么？",
             "options": {"A": "游泳", "B": "飞", "C": "走路", "D": "睡觉"},
             "answer": "A", "tip": "白鹅悠闲地浮在水面上游泳！",
             "hint": "提示：鹅是游泳高手~"},
        ]
    },
    "春晓": {
        "author": "孟浩然（唐）",
        "text": ["春眠不觉晓，处处闻啼鸟。", "夜来风雨声，花落知多少。"],
        "mood": "柔和温馨",
        "quiz_templates": [
            {"question": "春眠不觉晓，处处闻（      ）。",
             "options": {"A": "啼鸟", "B": "狗叫", "C": "鸡鸣", "D": "蛙声"},
             "answer": "A", "tip": "春天早上，到处都能听到鸟叫声~",
             "hint": "提示：春天到了，小鸟在唱歌~"},
            {"question": "夜来（      ）声，花落知多少？",
             "options": {"A": "风雨", "B": "雷声", "C": "雪落", "D": "水声"},
             "answer": "A", "tip": "晚上刮风下雨，好多花被吹落了~",
             "hint": "提示：想想春天的晚上，会下雨~"},
            {"question": "这首诗说的是哪个季节的故事？",
             "options": {"A": "春天", "B": "冬天", "C": "夏天", "D": "秋天"},
             "answer": "A", "tip": "春眠不觉晓——春天早上睡得很香~",
             "hint": "提示：春天百花盛开，鸟语花香~"},
        ]
    },
    "悯农": {
        "author": "李绅（唐）",
        "text": ["锄禾日当午，汗滴禾下土。", "谁知盘中餐，粒粒皆辛苦。"],
        "mood": "感恩珍惜",
        "quiz_templates": [
            {"question": "锄禾日当午，汗滴（      ）下土。",
             "options": {"A": "禾", "B": "米", "C": "土", "D": "菜"},
             "answer": "A", "tip": "农民伯伯种粮食，真辛苦！",
             "hint": "提示：禾是庄稼、小麦的意思~"},
            {"question": "谁知盘中餐，粒粒皆（      ）。",
             "options": {"A": "辛苦", "B": "快乐", "C": "美味", "D": "新鲜"},
             "answer": "A", "tip": "每一粒米饭都来之不易~",
             "hint": "提示：农民伯伯很辛苦~"},
            {"question": "这首诗告诉我们什么道理？",
             "options": {"A": "要珍惜粮食", "B": "要多睡觉", "C": "要努力读书", "D": "要帮助别人"},
             "answer": "A", "tip": "碗里的饭来之不易，不能浪费！",
             "hint": "提示：想想每天吃的饭是怎么来的~"},
        ]
    },
    "静夜思": {
        "author": "李白（唐）",
        "text": ["床前明月光，疑是地上霜。", "举头望明月，低头思故乡。"],
        "mood": "思念安静",
        "quiz_templates": [
            {"question": "床前明月光，疑是地上（      ）。",
             "options": {"A": "霜", "B": "雪", "C": "露水", "D": "雾气"},
             "answer": "A", "tip": "月光像白白的霜一样~",
             "hint": "提示：霜是白色的，秋天早上能在草上看到~"},
            {"question": "举头望（      ），低头思故乡。",
             "options": {"A": "明月", "B": "太阳", "C": "星星", "D": "白云"},
             "answer": "A", "tip": "抬头看天上圆圆的月亮~",
             "hint": "提示：晚上天上亮亮的是什么？~"},
            {"question": "这首诗里，月亮是什么颜色的？",
             "options": {"A": "白色（很亮）", "B": "黄色", "C": "红色", "D": "绿色"},
             "answer": "A", "tip": "明月光——月光很明亮，是白色的~",
             "hint": "提示：明月光就是很亮的白色月光~"},
        ]
    },
    "登鹳雀楼": {
        "author": "王之涣（唐）",
        "text": ["白日依山尽，黄河入海流。", "欲穷千里目，更上一层楼。"],
        "mood": "开阔向上",
        "quiz_templates": [
            {"question": "白日依山尽，黄河入（      ）流。",
             "options": {"A": "海", "B": "湖", "C": "江", "D": "河"},
             "answer": "A", "tip": "黄河一直流向大海~",
             "hint": "提示：黄河是中国最大的河，它流进了大海~"},
            {"question": "这首诗里说到了什么大河？",
             "options": {"A": "黄河", "B": "长江", "C": "珠江", "D": "京杭运河"},
             "answer": "A", "tip": "白日依山尽，黄河入海流~",
             "hint": "提示：中国有一条著名的黄色大河~"},
        ]
    },
}


# ─── 选项打乱 ────────────────────────────────────────────────────────────────
def shuffle_options(t: dict) -> dict:
    correct_key = t["answer"]
    correct_val = t["options"][correct_key]
    all_keys = ["A", "B", "C", "D"]
    wrong_keys = [k for k in all_keys if k != correct_key]
    wrong_vals = [t["options"][k] for k in wrong_keys]
    random_pos = random.choice(all_keys)
    shuffled = {random_pos: correct_val}
    remaining = [k for k in all_keys if k != random_pos]
    random.shuffle(wrong_vals)
    for i, k in enumerate(remaining):
        shuffled[k] = wrong_vals[i]
    return {
        **t,
        "options": shuffled,
        "answer": random_pos,
        "_correct_value": correct_val
    }


def load_questions(poem_name: str, seed: int = None):
    if seed is not None:
        random.seed(seed)
    templates = POEMS[poem_name]["quiz_templates"]
    shuffled = [shuffle_options(t) for t in templates]
    random.shuffle(shuffled)
    return shuffled


# ─── 状态读写 ──────────────────────────────────────────────────────────────
def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


# ─── AI输出JSON（供AI渲染交互界面）─────────────────────────────────────────
def output_json(poem_name: str, state: dict):
    """
    输出结构化 JSON，AI 读取后渲染为交互界面。
    使用传入的 state 字典，不重复读取文件。
    """
    poem = POEMS[poem_name]
    questions = [json.loads(q) for q in state["questions"]]
    results = state.get("results", [])
    q_idx = state["q_idx"]
    current_q = questions[q_idx]
    total = len(questions)

    done = len(results)
    score = sum(1 for r in results if r["correct"])

    payload = {
        # 元信息
        "type": "quiz",
        "poem": poem_name,
        "author": poem["author"],
        "poem_text": poem["text"],
        "mood": poem["mood"],
        # 进度
        "total": total,
        "done": done,
        "score": score,
        # 当前题
        "current": {
            "q_num": q_idx + 1,
            "question": current_q["question"],
            "options": current_q["options"],     # {"A": "文字", "B": "文字", ...}
            "correct_key": current_q["answer"],   # 仅供AI验证，不展示
            "_correct_value": current_q["_correct_value"],
            "hint": current_q.get("hint", ""),
            "tip": current_q["tip"],
        },
        # 已完成题（用于结果展示）
        "results": results,
        # 下题信息
        "next_hint": current_q.get("hint", ""),
    }

    # 如果测试已完成，附上汇总
    if q_idx >= total:
        payload["type"] = "summary"
        payload["final_score"] = score
        payload["final_total"] = total
        payload["correct_count"] = sum(1 for r in results if r["correct"])

    # 如果有本次操作结果（如答对/答错反馈），附在最后
    if "_result" in state and state["_result"]:
        payload["_result"] = state["_result"]

    print(json.dumps(payload, ensure_ascii=False, indent=2))


# ─── 处理用户回答（--resume 模式）───────────────────────────────────────────
def handle_answer(user_answer: str):
    """处理用户回答，返回结果并输出下一题的JSON"""
    state = load_state()
    if not state:
        print(json.dumps({"type": "error", "message": "没有找到保存的进度，请先运行：python3 quiz_engine.py 咏鹅"}))
        return

    poem_name = state["poem"]
    poem = POEMS[poem_name]
    questions = [json.loads(q) for q in state["questions"]]
    results = state.get("results", [])
    q_idx = state["q_idx"]
    hint_used = state.get("hint_used", False)
    attempts = state.get("attempts", 0)

    current_q = questions[q_idx]
    raw_upper = user_answer.strip().upper()

    # 提示请求
    if raw_upper in ("H", "提示", "HELP"):
        save_state({**state, "hint_used": True})
        output_json(poem_name, {
            **state,
            "_action": "hint_shown",
            "_hint": current_q.get("hint", ""),
        })
        return

    # 解析答案
    # 支持 A/B/C/D 或 0/1/2/3（按钮点击索引）
    ans = raw_upper
    for k in ["A", "B", "C", "D"]:
        if k == raw_upper or k in raw_upper or raw_upper in k:
            if raw_upper == k or raw_upper == f"选{k}":
                ans = k
                break
    # 支持数字索引 0/1/2/3（按钮点击）
    if ans not in ("A", "B", "C", "D"):
        try:
            idx = int(raw_upper)
            keys = ["A", "B", "C", "D"]
            if 0 <= idx < len(keys):
                ans = keys[idx]
        except ValueError:
            pass

    if ans not in ("A", "B", "C", "D"):
        output_json(poem_name, state)
        return

    attempts += 1
    is_correct = (ans == current_q["answer"])

    if is_correct:
        results.append({
            "question": current_q["question"],
            "correct": True,
            "attempts": attempts,
            "used_hint": hint_used,
            "user_answer": ans,
            "correct_key": current_q["answer"],
            "_correct_value": current_q["_correct_value"],
        })
        q_idx += 1
        hint_used = False
        attempts = 0
        result_payload = {
            "type": "correct",
            "q_num": q_idx - 1,
            "tip": current_q["tip"],
            "user_answer": ans,
            "correct_key": current_q["answer"],
            "_correct_value": current_q["_correct_value"],
            "progress": {"done": len(results), "total": len(questions), "score": sum(1 for r in results if r["correct"])},
        }
    else:
        if attempts >= 3:
            results.append({
                "question": current_q["question"],
                "correct": False,
                "attempts": 3,
                "used_hint": hint_used,
                "user_answer": ans,
                "correct_key": current_q["answer"],
                "_correct_value": current_q["_correct_value"],
            })
            q_idx += 1
            hint_used = False
            attempts = 0
            result_payload = {
                "type": "wrong_last",
                "q_num": q_idx - 1,
                "user_answer": ans,
                "correct_key": current_q["answer"],
                "_correct_value": current_q["_correct_value"],
                "progress": {"done": len(results), "total": len(questions), "score": sum(1 for r in results if r["correct"])},
            }
        else:
            result_payload = {
                "type": "wrong",
                "q_num": q_idx + 1,
                "user_answer": ans,
                "remaining": 3 - attempts,
                "hint": current_q.get("hint", ""),
            }

    # 完成？
    if q_idx >= len(questions):
        clear_state()
        print(json.dumps({
            **result_payload,
            "type": "summary",
            "poem": poem_name,
            "final_score": sum(1 for r in results if r["correct"]),
            "final_total": len(questions),
            "details": results,
        }, ensure_ascii=False, indent=2))
        return

    # 保存 + 出下一题
    next_q = questions[q_idx]
    save_state({
        "poem": poem_name,
        "questions": state["questions"],
        "results": results,
        "q_idx": q_idx,
        "hint_used": hint_used,
        "attempts": attempts,
    })
    output_json(poem_name, {
        "poem": poem_name,
        "questions": state["questions"],
        "results": results,
        "q_idx": q_idx,
        "hint_used": hint_used,
        "attempts": attempts,
        "_result": result_payload,
    })


# ─── 开始新测试 ─────────────────────────────────────────────────────────────
def start_quiz(poem_name: str, quiet: bool = False):
    poem = POEMS[poem_name]
    questions = load_questions(poem_name)
    state = {
        "poem": poem_name,
        "questions": [json.dumps(q, ensure_ascii=False) for q in questions],
        "results": [],
        "q_idx": 0,
        "hint_used": False,
        "attempts": 0,
    }
    save_state(state)
    if not quiet:
        print(json.dumps({"type": "started", "poem": poem_name, "author": poem["author"], "total": len(questions)}, ensure_ascii=False))
    output_json(poem_name, state)


# ─── 主入口 ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="幼儿古诗AI测试引擎 v4")
    parser.add_argument("poem", nargs="?", help="古诗名称")
    parser.add_argument("--resume", dest="resume", help="用户选择的答案（A/B/C/D/提示）")
    parser.add_argument("--quiet", action="store_true", help="静默模式（无装饰）")
    parser.add_argument("--reset", action="store_true", help="重置进度，重新开始")
    args = parser.parse_args()

    # 重置
    if args.reset:
        clear_state()
        print(json.dumps({"type": "reset"}))
        return

    # 开始新测试
    if args.poem:
        if args.poem not in POEMS:
            print(json.dumps({"type": "error", "message": f"找不到：{args.poem}，可用：{', '.join(POEMS.keys())}"}))
            return
        if args.resume:
            handle_answer(args.resume)
        else:
            start_quiz(args.poem, args.quiet)
        return

    # 无参数：读断点
    state = load_state()
    if not state:
        print(json.dumps({
            "type": "menu",
            "poems": [{"name": k, "author": v["author"], "lines": v["text"]} for k, v in POEMS.items()]
        }))
        return

    output_json(state["poem"], state)


if __name__ == "__main__":
    main()
