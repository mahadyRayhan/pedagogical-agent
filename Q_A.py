import os
import time
import glob
import json
import google.generativeai as genai
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import evaluate
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from nltk.translate.chrf_score import sentence_chrf
from google.generativeai.types import StopCandidateException
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from sacrebleu.metrics import BLEU
from bert_score import score as bert_score

load_dotenv()

# Initialize GenAI with API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class GeminiQuestion_and_Answering:
    def __init__(self):
        self.model = None
        self.safety_settings = None
        self.embed_model = None
        self.files = None
        self.chat_session = None
        self.evaluation_data = None
        self.rouge = evaluate.load("rouge")
        self.bleu = evaluate.load("bleu")
        self.meteor = evaluate.load("meteor")
        self.sacrebleu = BLEU()

    def load_resources(self, load_resource=False):
        if load_resource or not self.files:
            file_paths = glob.glob("uSucceed_resource/*.pdf")
            self.files = self.upload_to_gemini(file_paths, mime_type="application/pdf")
            self.wait_for_files_active(self.files)
            self.configure_genai()

        if not self.embed_model:
            self.embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
    def upload_to_gemini(self, paths, mime_type=None):
        files = []
        for path in paths:
            file = genai.upload_file(path, mime_type=mime_type)
            print(f"Uploaded file '{file.display_name}' as: {file.uri}")
            files.append(file)
        return files

    def wait_for_files_active(self, files):
        print("Waiting for file processing...")
        for name in (file.name for file in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(10)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")
        print("...all files ready\n")
    
    def configure_genai(self):
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        generation_config = {
            "temperature": 0,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)
        self.chat_session = self.model.start_chat()

    def ask_question(self, question):
        print(question)
        final_prompt = f"You are a question answering model. Please answer the following question briefly and to the point. The question is: {question}"
        response = self.chat_session.send_message(final_prompt, safety_settings=self.safety_settings)
        return response.text

    def load_evaluation_data(self):
        with open("evaluation_example.json", "r") as f:
            self.evaluation_data = json.load(f)
        print("Loaded evaluation data successfully.")
    
    def evaluate(self):
        if not self.evaluation_data:
            self.load_evaluation_data()

        results = []
        for i, data in enumerate(self.evaluation_data['evaluation_data']):
            question = data["question"]
            expected_answer = data["answer"]
            generated_answer = self.ask_question(question)

            rouge_result = self.rouge.compute(predictions=[generated_answer], references=[expected_answer])
            bleu_result = self.bleu.compute(predictions=[generated_answer], references=[[expected_answer]])
            meteor_result = self.meteor.compute(predictions=[generated_answer], references=[expected_answer])
            sacrebleu_result = self.sacrebleu.corpus_score([generated_answer], [[expected_answer]])
            chrf_score = sentence_chrf(expected_answer, generated_answer)

            P, R, F1 = bert_score([generated_answer], [expected_answer], lang="en", verbose=False)

            reference_embedding = self.embed_model.embed_query(expected_answer)
            generated_embedding = self.embed_model.embed_query(generated_answer)
            cosine_sim = cosine_similarity([reference_embedding], [generated_embedding])[0][0]

            exact_match = 1 if generated_answer.lower() == expected_answer.lower() else 0
            f1 = self.compute_f1(expected_answer, generated_answer)

            results.append({
                "question_id": i,
                "rouge1": rouge_result["rouge1"],
                "rouge2": rouge_result["rouge2"],
                "rougeL": rouge_result["rougeL"],
                "bleu": bleu_result["bleu"],
                "sacrebleu": sacrebleu_result.score,
                "meteor": meteor_result["meteor"],
                "chrf": chrf_score,
                "bert_score_f1": F1.item(),
                "cosine_similarity": cosine_sim,
                "exact_match": exact_match,
                "f1_score": f1
            })
        self.visualize_results(results)

    def visualize_results(self, results):
        df = pd.DataFrame(results)
        fig, axes = plt.subplots(3, 2, figsize=(20, 24))

        rouge_avg = df[["rouge1", "rouge2", "rougeL"]].mean()
        rouge_avg.plot(kind="bar", ax=axes[0, 0], color=["blue", "green", "red"])
        axes[0, 0].set_title("Average ROUGE Scores")
        axes[0, 0].set_ylabel("Score")
        axes[0, 0].set_xlabel("ROUGE Metrics")
        axes[0, 0].text(0, rouge_avg[0], "Average Rouge-1 score shows lexical overlap.", ha="center", va="bottom")

        df[["bleu", "sacrebleu", "meteor", "chrf"]].melt().plot(kind="box", ax=axes[0, 1])
        axes[0, 1].set_title("Distribution of BLEU, SacreBLEU, METEOR, and chrF Scores")
        axes[0, 1].set_ylabel("Score")
        axes[0, 1].set_xlabel("Metrics")
        axes[0, 1].text(0, df[["bleu", "sacrebleu"]].mean().mean(), "Boxplot showing score distribution.", ha="center", va="bottom")

        axes[1, 0].scatter(df["bert_score_f1"], df["cosine_similarity"])
        axes[1, 0].set_title("BERTScore F1 vs Cosine Similarity")
        axes[1, 0].set_xlabel("BERTScore F1")
        axes[1, 0].set_ylabel("Cosine Similarity")
        axes[1, 0].text(0.5, 0.9, "Shows relationship between semantic and embedding similarity.", ha="center", va="bottom")

        df[["exact_match", "f1_score"]].mean().plot(kind="bar", ax=axes[1, 1])
        axes[1, 1].set_title("Average Exact Match and F1 Score")
        axes[1, 1].set_ylabel("Score")
        axes[1, 1].text(0.5, df["f1_score"].mean(), "F1 score diagram shows correctness of answers.", ha="center", va="bottom")

        corr_matrix = df.drop("question_id", axis=1).corr()
        sns.heatmap(corr_matrix, ax=axes[2, 0], cmap="coolwarm", annot=True, fmt=".2f", cbar_kws={"label": "Correlation"})
        axes[2, 0].set_title("Correlation Between Metrics")
        axes[2, 0].text(0.5, 0.9, "Heatmap showing correlation between evaluation metrics.", ha="center", va="bottom")

        df["cosine_similarity"].hist(ax=axes[2, 1], bins=20)
        axes[2, 1].set_title("Distribution of Cosine Similarities")
        axes[2, 1].set_xlabel("Cosine Similarity")
        axes[2, 1].set_ylabel("Frequency")
        axes[2, 1].text(0.5, 0.9, "Histogram showing distribution of similarity scores.", ha="center", va="bottom")

        plt.tight_layout()
        plt.show()

    def compute_f1(self, a_gold, a_pred):
        gold_toks = set(a_gold.lower().split())
        pred_toks = set(a_pred.lower().split())
        common = gold_toks & pred_toks
        if len(gold_toks) == 0 or len(pred_toks) == 0:
            return int(gold_toks == pred_toks)
        if len(common) == 0:
            return 0
        precision = len(common) / len(pred_toks)
        recall = len(common) / len(gold_toks)
        return (2 * precision * recall) / (precision + recall)


# Main function to handle querying and evaluation
def gemini_qa_system(query="", load_resource=True, evaluate=True):
    gemini_qa = GeminiQuestion_and_Answering()

    if load_resource:
        gemini_qa.load_resources(load_resource=True)
    
    if evaluate:
        gemini_qa.evaluate()
    elif query:
        answer = gemini_qa.ask_question(query)
        print(f"Generated Answer: {answer}")

# Example usage:
# gemini_qa_system(query="What is the capital of France?", load_resource=False, evaluate=False)
# gemini_qa_system(load_resource=False, evaluate=True)
