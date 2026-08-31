# Sprint Günlüğü

DeCode IDE'nin sprint kayıtları. Her sprint kendi dosyasında durur; biten
sprintler arşiv olarak olduğu gibi kalır, yeni iş her zaman yeni bir dosyaya
yazılır. Uzun vadeli plan için [Roadmap](../Roadmap.md)'e bakın.

**Aktif sprint:** yok — [Sprint 07](sprint-07.md) ile Faz 2 kapandı.

| Sprint | Tarih | Başlık | Durum |
|---|---|---|---|
| [01](sprint-01.md) | 02 Tem 2026 | Temeller: iskelet, editör, sidebar | Tamamlandı |
| [02](sprint-02.md) | 06–11 Tem 2026 | Modal çekirdek ve kısayollar | Tamamlandı |
| [03](sprint-03.md) | 25 Ağu 2026 | Komut satırı ve durum çubuğu | Tamamlandı |
| [04](sprint-04.md) | 28 Ağu 2026 | Tamamlama ve editör cilası | Tamamlandı |
| [05](sprint-05.md) | 31 Ağu 2026 | Sekmeler, terminal, kaydırılabilir öneriler | Tamamlandı |
| [06](sprint-06.md) | 31 Ağu 2026 | Telescope ve depo hijyeni | Tamamlandı |
| [07](sprint-07.md) | 31 Ağu 2026 | Dosya içi arama, değiştirme, sembol atlama | Tamamlandı |

## Yeni sprint nasıl açılır

1. Aşağıdaki şablonu `sprint-NN.md` olarak kaydet; başlığı, tarihi ve durumu doldur.
2. Bir önceki sprintin **Devreden** maddelerini yeni sprintin **Çıktılar**ının başına taşı.
3. Yukarıdaki tabloya bir satır ekle, "Aktif sprint" satırını güncelle ve
   [Roadmap](../Roadmap.md)'te ilgili fazı işaretle.

## Şablon

```markdown
# Sprint NN — <başlık>
**Tarih:** <tarih aralığı> · **Durum:** Tamamlandı / Aktif · **Commit(ler):** <kısa hash + mesaj>

## Hedef
Tek cümlelik sprint hedefi.

## Çıktılar
- [x] <iş> — `dosya/yolu.py`

## Teknik notlar
Karar ve tuzak notları (neden böyle yapıldı).

## Devreden
Bu sprintte bitmeyip sonrakine kalanlar.
```
