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
- v3 (solve_v3.py): bulmaca başına 5 sabit kümesi dene, en iyiyi al → 236,654.
- Sonraki fikirler: sabit kümesini bulmaca başına optimize etmek, önceki hedefleri/ara değerleri yeniden kullanmak, C++ ile daha geniş arama.
- Kaggle LB (2026-11-19): v2 = 244,583 (lokal ile aynı). Lider ≈130,845 (≈4.9/hedef).
- Alıştırma analizi: shared/mixed ailelerinde hedefler ≈ önceki_hedef*küçük + küçük_fark; independent'ta ilişki yok → güçlü arama (MITM) gerek.
- Kaggle CLI çalışıyor (anahtar sadece ~/.kaggle'da, proje klasöründe DEĞİL). merge.py: doğrulanmış submission'ları bulmaca bazında birleştirir.
- Public notebook çıktıları + v3 birleşimi: 138,557 (Kaggle'da teyitli), sıra 113/1045. Lider 130,845.
- opt/resynth.cpp: özel koni (private cone) yeniden sentezi, derinlik ≤4 (MITM). Bizim v3'te büyük kazanç; public portföyde derinlik 3'te 0, derinlik 4'te ~0.05/bulmaca. Public programlar yerel olarak çok cilalı.
- Hedef başına özel koni boyutu (public en iyi): 1:7780 2:6983 3:5038 4:3139 5:2191 6:1098 7:490 8:178.
