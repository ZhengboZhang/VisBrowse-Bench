import os
import json
import jsonlines
from openai import OpenAI
import argparse

judge_prompt = """
You are a rigorous question-and-answer quality assessment expert. Given a question, your task is to compare the "groud truth" and the "model answer", determine whether they are semantically equivalent, and output "yes" or "no".
question: {}
ground truth: {}
model answer: {}
"""

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

def LLM_as_Judge(question, gt, answer):

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    completion = client.chat.completions.create(
        model=os.getenv('MODEL_NAME', ''),
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": judge_prompt.format(question, gt, answer)},
                ],
            },
        ],
    )
    return completion.choices[0].message.content

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--result_path", type=str, required=True)
    parser.add_argument("--judge_path", type=str, required=True)
    args = parser.parse_args()

    data_path = args.result_path

    data = []
    with jsonlines.open(data_path) as reader:
        for item in reader:
            data.append(item)

    all = 0
    corr = 0
    ans = []
    for item in data[0:]:
        all += 1
        idx = item['id']
        answer = item['gen']
        question = item['question']
        gt = item['answer']
        if len(gt) > 1:
            gt = "; ".join(gt)
        else:
            gt = gt[0]
        if answer == 'No answer':
            ans.append({"id": idx, "gt": gt, "answer": answer, "judge": 'no'})
            continue
        if answer == gt:
            corr += 1
            ans.append({"id": idx, "gt": gt, "answer": answer, "judge": 'yes'})
            continue

        res = LLM_as_Judge(question, gt, answer)
        if res == 'yes':
            corr += 1
        ans.append({"id": idx, "gt": gt, "answer": answer, "judge": res})
        print(f"Ground truth:{gt}, \t Answer: {answer}, \t Judgement: {res}")

    print(f"Correct answers: {corr}")
    print(f"Total questions: {all}")
    print(f"Accuracy: {corr/all}")
    with open(os.path.join(args.judge_path, data_path.split('/')[-1]), 'a', encoding='utf-8') as f:
        for aa in ans:
            json_line = json.dumps(aa, ensure_ascii=False)
            f.write(json_line + '\n')