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
- 2026-11-19: güncel public çıktılar + resynth → submission_best.csv = 138,455 (Kaggle teyitli, sıra 104/1072). Lider 130,820.
- Maliyet yapısı: ilk hedef ≈20.6 talimat (sabit kurulumu), sonraki hedefler ≈4.35. Bit boyuna göre: 40-bit 4.72/hedef, 50-bit 5.37, 60-bit 7.55.
- beam/tony_solver.cpp: Tony Li beam çözücüsü (Apache 2.0), palet/yaprak parametreli. Tek çalıştırma (varsayılan) 20 bulmacada 3293 vs en iyi 2374 → palet varyasyonu tek başına umut vermiyor.
- resynth derinlik 5-6 kofaktör araması (t = q*B ± c): birim testte doğru çalışıyor (63→5), ama 24 zor public bulmacada 0 kazanç. Public programlar tek-hedef yerel hamlelerde tükenmiş durumda.
- Hard puzzle yapısı: hedefler genelde t = X*Y ± küçük, X ve Y orta boy (20–40 bit) ve çok kez paylaşılan ara değerler.
- Paylaşılan düğüm sökme (sharedrm, MODE 4): v3'te +221/20 bulmaca, public'te 0 (derinlik 3 ve 4).
- Alıştırma hedeflerinde gizli ortak çarpan yok (ofset ±40 ile gcd ~ rastgele seviye), sadece shared/multiplicative ailelerde t≈k·u ilişkisi.
- 2026-11-20: Register baskısı: en iyi programların 403'ünde max canlı değer 44–48; bunlar en pahalı bulmacalar (50-bit: 6.75 vs 3.93 /hedef). Toplam ~78k talimat. Georgy (discussion): >48 canlı planlar ~%9 kısa. Yerel hamleler sınırsız register'da bile 0 → kazanç üretici (planner+scheduler) aşamasında.
- Otomatik hat 2026-11-20 09:08 UTC: 135,442 (sıra 180/1718, lider 128,831).
- sched/sched.py: plan→48 register zamanlayıcı (Belady + maliyet-duyarlı yeniden hesaplama, COSTPOW=2). En zor 20 bulmacada Tony derleyicisinden iyi: 88 yaprak 5834→5362, 130 yaprak 5777→5471. Ama ham programlar en iyiden bulmaca başına +25..+88 kötü (public yeniden yazma yığını ~%25 kazandırıyor).
- resynth donor modu (argv[6] bağışçı dosyası, MAXD=0): 185 public CSV'den tarif nakli → en iyide 0 kazanç (v3'te 307).
- 2026-11-20 portföy denemesi: 20 zor bulmacada 10 ayar × (Tony beam + sched.py), bulmaca başına min = 5181 vs en iyi 4336 (+%19.5; her bulmacada +25..+58). Tek çalıştırmalar 5281–5553. Sonuç: bu yoldan en iyiye yaklaşılamıyor → araştırma durduruldu, sadece otomatik takip.
