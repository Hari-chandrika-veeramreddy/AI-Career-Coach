# Models Directory

This directory can hold optional local AI/ML model artifacts or offline checkpoints if pre-downloaded.

The application automatically downloads/caches required models (Sentence Transformers, Faster-Whisper, spaCy en_core_web_sm) in the default system cache using `@st.cache_resource`.
