import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Jalur folder di sistem Linux RunPod (sesuaikan jika nama foldernya berbeda)
base_model_id = "Qwen/Qwen2.5-7B-Instruct" 
lora_path = "/workspace/qwen_alodokter_lora"
output_dir = "/workspace/qwen_alodokter_merged"

# 1. Memuat Base Model langsung ke GPU (CUDA)
print("1. Memuat Base Model ke GPU...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id, 
    torch_dtype=torch.bfloat16, 
    device_map="cuda"  # Memuat langsung ke GPU RunPod yang super cepat
)
tokenizer = AutoTokenizer.from_pretrained(base_model_id)

# 2. Memuat dan Menggabungkan LoRA Adapter
print("2. Memuat dan Menggabungkan LoRA Adapter...")
model = PeftModel.from_pretrained(base_model, lora_path)
merged_model = model.merge_and_unload()

# 3. Menyimpan Model Hasil Merge (Tanpa limit shard size)
print("3. Menyimpan Model Hasil Merge...")
merged_model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

print("\nSelesai! Model sukses digabungkan di RunPod GPU.")
print("Silakan cek folder hasil merge Anda di:", output_dir)