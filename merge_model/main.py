import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Jalur folder di Drive E
base_model_id = "Qwen/Qwen2.5-7B-Instruct" 
lora_path = r"E:\ModelConfig\qwen_alodokter_lora"
output_dir = r"E:\ModelConfig\qwen_alodokter_merged"
cache_dir = r"E:\ModelConfig\hf_cache"

print("1. Memuat Base Model dari Cache Lokal (Drive E)...")
# Menggunakan CPU & menghemat RAM saat memuat model
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id, 
    torch_dtype=torch.bfloat16, 
    device_map="cpu",
    cache_dir=cache_dir,
    low_cpu_mem_usage=True,   # <-- Menghemat RAM saat proses load
    local_files_only=True     # <-- Memaksa menggunakan file offline yang sudah Anda unduh
)
tokenizer = AutoTokenizer.from_pretrained(
    base_model_id,
    cache_dir=cache_dir,
    local_files_only=True     # <-- Memaksa menggunakan tokenizer offline
)

print("2. Memuat dan Menggabungkan LoRA Adapter...")
model = PeftModel.from_pretrained(base_model, lora_path)
merged_model = model.merge_and_unload()

print("3. Menyimpan Model Hasil Merge (Mencicil per 2GB)...")
# max_shard_size="2GB" akan memecah file agar RAM komputer Anda tidak MemoryError lagi
merged_model.save_pretrained(output_dir, max_shard_size="2GB")
tokenizer.save_pretrained(output_dir)

print("\nSelesai! Model sukses digabungkan tanpa MemoryError.")
print("Silakan cek folder hasil merge Anda di:", output_dir)