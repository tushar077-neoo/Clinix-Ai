# 🧠 Clinix AI — PDF-Based Health Analysis & Recommendation System

Clinix AI is an AI-powered health analysis system that extracts clinical parameters from blood report PDFs, interprets them using a Large Language Model (LLM), and suggests possible health conditions along with nearby clinic recommendations.

---

## 🚀 Features

* 📄 Upload and analyze blood report PDFs
* 🔍 Automatic extraction of key health parameters
* 🤖 AI-powered interpretation using LLM (Groq)
* 📊 Interactive health data visualization using Plotly
* 📍 Nearby clinic suggestions via Google Maps integration
* ⚡ Fast and simple UI built with Streamlit

---

## 🧠 How It Works

1. User uploads a blood report (PDF)
2. Text is extracted using pdfplumber
3. Key parameters are parsed using regex
4. Extracted data is analyzed using LLM (Groq)
5. Health insights and possible conditions are generated
6. Results are visualized and relevant clinics are suggested

---

## 🛠️ Tech Stack

* Python
* Streamlit
* pdfplumber
* Groq (LLM API)
* Plotly
* Regex (Data Extraction)
* Google Maps API

---

## 📦 Installation & Setup

```bash
git clone https://github.com/tushar077-neoo/Clinix-Ai.git
cd Clinix-Ai
pip install -r requirements.txt
streamlit run app.py
```

---

## ⚠️ Limitations

* Works best with digitally generated (text-based) PDF reports
* May not perform well on scanned/image-based reports
* Extraction depends on report format and keyword consistency
* AI-generated insights are not medically verified

---

## ⚠️ Disclaimer

This project is for educational purposes only and should not be used as a substitute for professional medical advice, diagnosis, or treatment.

---

## 🔮 Future Improvements

* Support for scanned reports using OCR
* Improved parameter extraction with NLP
* Multi-condition ranking with confidence scores
* Chatbot-based interaction
* Mobile application version

---

## 📁 Project Structure

```
Clinix-Ai/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── utils/
├── data/
└── sample_reports/
```

---

## 💡 Key Highlights

* End-to-end pipeline: PDF → Extraction → AI → Visualization → Recommendation
* Combines traditional parsing with modern LLM-based reasoning
* Real-world inspired problem-solving approach

---

## 🤝 Contribution

Feel free to fork the repository and improve the system. Contributions are welcome!

---

## ⭐ Support

If you found this project useful, consider giving it a star ⭐ on GitHub.

* Advanced diagnostics with deep learning
