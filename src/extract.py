import os
import base64

from dotenv import load_dotenv
from pdf2image import convert_from_path
from openai import OpenAI

# ---------- CONFIG ----------
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
path = 'C:\\Users\\Arigo\\PycharmProjects\\malindo-extractor\\src\\source'
for filename in os.listdir(path):
    OUTPUT_DIR = "images"
    PAGE_TO_EXTRACT = 1

    PROMPT = """
    # 📄 PDF / IMAGE DOCUMENT EXTRACTOR PROMPT
    ## (SKA & PIB)
    
    ---
    
    ## 🎯 PERAN AGENT
    Kamu adalah **Document Extraction Agent**.
    
    Kamu akan menerima **dokumen PDF yang telah dikonversi menjadi IMAGE**.
    Dokumen hanya terdiri dari **dua jenis**:
    - **SKA (Surat Keterangan Asal)**
    - **PIB (Pemberitahuan Impor Barang)**
    
    Tugas utama:
    1. Mengidentifikasi **jenis dokumen**
    2. Mengekstrak data **berdasarkan nomor atribut yang tercetak pada dokumen**
    3. Menghasilkan output **JSON valid**
    4. Tidak menambahkan asumsi, interpretasi, atau data di luar dokumen
    5. Jika data tidak ditemukan, isi dengan `null`
    
    ---
    
    ## 📌 ATURAN UMUM EKSTRAKSI
    - Nomor atribut **mengacu langsung ke nomor yang tercetak di dokumen**
    - Jangan menebak nilai atribut
    - Jika satu atribut berisi lebih dari satu informasi, pisahkan sesuai kebutuhan field
    - Format tanggal: `YYYY-MM-DD` (jika memungkinkan)
    - Checkbox: **ambil value yang dicentang saja**
    - Stempel & tanda tangan: **boolean (`true` / `false`)**
    - Jika field tidak ditemukan → `null`
    
    ---
    
    ## 📑 EKSTRAKSI DOKUMEN SKA
    
    Ambil data **hanya dari atribut berikut**:
    
    | No | Field JSON | Sumber Atribut |
    |----|-----------|----------------|
    | 1  | tanggal | Atribut nomor **10** |
    | 2  | nomor | Atribut nomor **10** |
    | 3  | nomor_referensi | Atribut **reference** |
    | 4  | tanggal_penerbitan | Atribut nomor **12** |
    | 5  | nama_pengirim | Atribut nomor **1** |
    | 6  | negara_pengirim | Atribut nomor **11** |
    | 7  | tanggal_departure | Atribut nomor **3** |
    | 8  | sarana | Atribut nomor **3** |
    | 9  | voy_flight | Atribut nomor **3** code dari sarana |
    | 10 | uraian_barang | Atribut nomor **7** |
    | 11 | hs_code | Atribut nomor **7** |
    | 12 | quantity | Atribut nomor **9** |
    | 13 | origin_criteria | Atribut nomor **8** |
    | 14 | stempel_ttd_attr_11 | Atribut nomor **11** (`true/false`) |
    | 15 | stempel_ttd_attr_12 | Atribut nomor **12** (`true/false`) |
    | 16 | checkbox_attr_13 | Atribut nomor **13** (yang dicentang) |
    
    ---
    
    ## 📑 EKSTRAKSI DOKUMEN PIB
    
    Ambil data berikut:
    
    | No | Field JSON | Sumber |
    |----|-----------|--------|
    | 1  | nomor_pengajuan | Dokumen PIB |
    | 2  | nomor_pib | Dokumen PIB |
    | 3  | nomor_dan_tanggal_pendaftaran | Dokumen PIB |
    | 4  | kode_fasilitas | Atribut nomor **20** |
    | 5  | nama_pengirim | Dokumen PIB |
    | 6  | negara_pengirim | Dokumen PIB |
    
    ---
    
    ## 🧾 FORMAT OUTPUT JSON
    
    ### ✅ Contoh Output SKA
    ```json
    {
      "filename": namafile_sumber,
      "document_type": "SKA",
      "tanggal": "2024-05-10",
      "nomor": "SKA-12345",
      "nomor_referensi": "REF-998877",
      "tanggal_penerbitan": "2024-05-12",
      "nama_pengirim": "PT ABC Indonesia",
      "negara_pengirim": "Indonesia",
      "tanggal_departure": "2024-05-15",
      "sarana": "MV OCEAN STAR",
      "voy_flight": "VY123",
      "uraian_barang": "Textile products",
      "hs_code": "5208.39",
      "quantity": "1000 KG",
      "origin_criteria": "WO",
      "stempel_ttd_attr_11": true,
      "stempel_ttd_attr_12": false,
      "checkbox_attr_13": ["Option A"]
    }
    
    ## 🚫 LARANGAN
    Jangan menambahkan field di luar spesifikasi
    
    Jangan memperbaiki ejaan atau menafsirkan data
    
    Jangan menggabungkan SKA dan PIB dalam satu output
    
    Output HARUS JSON VALID

    """

    # ---------- SETUP ----------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    client = OpenAI(api_key='')

    # ---------- STEP 1: PDF → IMAGE ----------
    print("Converting PDF to image...")
    images = convert_from_path(f'{path}\\{filename}', dpi=600, poppler_path=POPPLER_PATH)

    image_path = os.path.join(OUTPUT_DIR, f"page_{PAGE_TO_EXTRACT}.png")
    images[PAGE_TO_EXTRACT - 1].save(image_path, "PNG")

    # ---------- STEP 2: IMAGE → BASE64 ----------
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    # ---------- STEP 3: SEND TO OPENAI VISION ----------
    print("Sending image to OpenAI...")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        },
                    },
                ],
            }
        ],
        temperature=0
    )

    # ---------- RESULT ----------
    result = response.choices[0].message.content
    print("\nExtracted Result:")
    print(result)
