# Santa 2026 – proje notları (yeni thread'ler önce bunu okusun)

## Hedef ve tercihler
- Hedef: ilk sıralar (+ Rudolph Prize: erken/sık submit önemli). Final: 28 Ocak 2027.
- Dil: Python prototip, ağır arama C++. Kullanıcının Kaggle, GitHub, Hugging Face hesabı var.
- Kullanıcı Türkçe yazıyor.

## Kurallar (Evaluation sayfası)
- Skor = 1000 programın toplam talimat sayısı (düşük iyi). Program: [op,a,b,dst], 48 register, <=4096 talimat.
- Değerler pozitif tam sayı, <= value_limit. Varsayım: '/' tam bölme; hedef herhangi bir anda register'da görünmeli (örnek submission bu varsayımla geçerli).

## Durum
- data/: puzzles.csv, practice_puzzles.csv, sample_submission.csv
- validate.py: lokal skorlayıcı. Örnek submission = 1,490,379.
- baseline.py: signed-digit Horner, taban 2D+1 → 328,117 (≈12.2 talimat/hedef).
- practice lower_bound = hedef sayısı (önemsiz alt sınır), yapı ipucu DEĞİL.
- v2 (solve_v2.py + beam.py): sabitler 1..24 + asallar ~113'e kadar register'da; her hedef beam search ile t=q*m±d → 244,583 (≈9.1/hedef). 16 bulmacada fallback baseline.
- Sonraki fikirler: sabit kümesini bulmaca başına optimize etmek, önceki hedefleri/ara değerleri yeniden kullanmak, C++ ile daha geniş arama.
