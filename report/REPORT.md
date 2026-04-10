# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Lê Trung
**Nhóm:** 
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Trong không gian vector, hai câu có highcosine similarity nghĩa là chúng có ý nghĩa ngữ nghĩa gần nhau. Càng gần 1 thì mức tương đồng càng cao.

**Ví dụ HIGH similarity:**
- Sentence A: Python là ngôn ngữ lập trình nổi tiếng trong ngành khoa học dữ liệu
- Sentence B: Python được sử dụng phổ biến trong ngành khoa học dữ liệu và lập trình
- Tại sao tương đồng: Cùng nói về Python được dùng nhiều trong lập trình và khoa học dữ liệu

**Ví dụ LOW similarity:**
- Sentence A: Python là ngôn ngữ lập trình nổi tiếng trong ngành khoa học dữ liệu
- Sentence B: Bánh chưng là món ăn Tết truyền thống của người Việt 
- Tại sao khác: 2 câu nói về 2 chủ đều hoàn toàn khác nhau, gần như không có liên hệ về mặt ngữ nghĩa

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector, nên đo được mức giống nhau về ngữ nghĩa tốt hơn. Với text embeddings, độ dài vector thường ít quan trọng hơn hướng biểu diễn ý nghĩa.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> *Đáp án: Step = 500-50 = 450. Số chunk = ceil((10000 - 500) / 450) + 1 = 23 

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Overlap tăng thì số step giảm, số chunk sẽ tăng lên. Overlap để tránh trường hợp edgecase khi thông tin quan trọng ở phần cuối chunk, giảm tình trạng mất ngữ cảnh.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Vietnamese Cooking Recipes 

**Tại sao nhóm chọn domain này?**
> Các tài liệu công thức nấu ăn có cấu trúc rất rõ ràng, bao gồm các phần cố định như Giới thiệu, Nguyên liệu và Các bước thực hiện. Cấu trúc này rất phù hợp để đánh giá xem chiến lược chunking có bảo toàn được trọn vẹn ngữ cảnh của một bước nấu hay danh sách nguyên liệu hay không. Đồng thời, nó cho phép tạo ra các benchmark queries thực tế và phong phú.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Savory Pancakes | Vietnamtourism | 1208 | Introduce, Ingredients, Processọt |
| 2 | Braised Tofu with Quail Eggs | Vietnamtourism | 2470 | Introduce, Ingredients, Processọt |
| 3 | Duck Porridge & Salad (Cháo Gỏi Vịt) | Vietnamtourism | 1970 | Introduce, Ingredients, Processọt |
| 4 | Grilled Snails with Salt & Chili | Vietnamtourism | 1012 | Introduce, Ingredients, Processọt |
| 5 | Orange Fruit Skin Jam (Mứt vỏ cam) | Vietnamtourism | 1225 | Introduce, Ingredients, Processọt |

### Metadata Schema

| Trường metadata | Kiểu           | Ví dụ giá trị                             | Tại sao hữu ích cho retrieval? |
|-----------------|----------------|-------------------------------------------|--------------------------------|
| introduce       | string         | "Món bánh khọt miền Nam, ăn kèm rau..."   | Tóm tắt ngữ nghĩa → match query mô tả (VD: món mùa đông, món cho trẻ em) |
| ingredients     | list[string]   | ["tofu", "quail eggs", "fish sauce"]      | Cho phép tìm theo nguyên liệu (VD: món có trứng cút, món có tôm) |
| process         | list[string]   | ["boil eggs", "cook tofu", "braise..."]   | Hỗ trợ tìm kiếm ngữ nghĩa theo hành động (VD: món nướng, món kho) |
---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| `Braised_Tofu.md` | FixedSizeChunker (`fixed_size`) | 3 | 436.67 | Medium |
| `Braised_Tofu.md` | SentenceChunker (`by_sentences`) | 3 | 398.00 | Good |
| `Braised_Tofu.md` | RecursiveChunker (`recursive`) | 4 | 301.75 | Good |
| `Duck_Porridge.md` | FixedSizeChunker (`fixed_size`) | 6 | 453.33 | Medium |
| `Duck_Porridge.md` | SentenceChunker (`by_sentences`) | 6 | 406.33 | Good |
| `Duck_Porridge.md` | RecursiveChunker (`recursive`) | 7 | 352.00 | Good |
| `Orange_Fruit_Skin_Jam.md` | FixedSizeChunker (`fixed_size`) | 3 | 442.00 | Medium |
| `Orange_Fruit_Skin_Jam.md` | SentenceChunker (`by_sentences`) | 4 | 301.25 | Good |
| `Orange_Fruit_Skin_Jam.md` | RecursiveChunker (`recursive`) | 4 | 305.75 | Good |


### Strategy Của Tôi

**Loại:** FixedSizeChunker

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **của tôi** | | | |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Viết 2-3 câu: dùng regex gì để detect sentence? Xử lý edge case nào?*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Viết 2-3 câu: algorithm hoạt động thế nào? Base case là gì?*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Viết 2-3 câu: lưu trữ thế nào? Tính similarity ra sao?*

**`search_with_filter` + `delete_document`** — approach:
> *Viết 2-3 câu: filter trước hay sau? Delete bằng cách nào?*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Viết 2-3 câu: prompt structure? Cách inject context?*

### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** __ / __

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | high / low | | |
| 2 | | | high / low | | |
| 3 | | | high / low | | |
| 4 | | | high / low | | |
| 5 | | | high / low | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | "What ingredients are needed for braised tofu with quail eggs?" |"100-200g fried tofu slices, 15-20 quail eggs, spring onion, shallot, salt, fish sauce, sugar, pepper, soy sauce, and Maggi's seasoning powder." |
| 2 | "How do you make the dipping sauce for grilled snails?"| "Mix salt, pepper, lemon juice, and sugar together. Serve with Vietnamese mint herb." |
| 3 | "What is the process for making duck porridge?" | "Boil duck with ginger and grilled onion. Roast sticky rice separately, then cook in broth until soft. Season and top with fried purple onion and pepper."|
| 4 | "Which dish is a dessert and how is it stored?" | "Orange Fruit Skin Jam (Mut Vo Cam). After cooking, wait to cool, then store in a jar and use day by day." |
| 5 | "Which dishes require shrimp as an ingredient?" | "Vietnamese Mini Savory Pancakes (Banh Khot) require fresh shrimps (10 pieces, boiled and cut in half) and dried shrimp (100g, ground well)." |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
