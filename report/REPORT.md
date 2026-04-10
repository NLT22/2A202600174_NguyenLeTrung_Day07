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
| 1 | Savory Pancakes (Bánh Khọt) | vietnamtourism | 1981 | source, extension, category, difficulty, doc_id, chunk_index |
| 2 | Braised Tofu with Quail Eggs | vietnamtourism | 1210 | source, extension, category, difficulty, doc_id, chunk_index |
| 3 | Duck Porridge & Salad (Cháo Gỏi Vịt) | vietnamtourism | 2470 | source, extension, category, difficulty, doc_id, chunk_index |
| 4 | Grilled Snails with Salt & Chili | vietnamtourism | 1014 | source, extension, category, difficulty, doc_id, chunk_index |
| 5 | Orange Fruit Skin Jam (Mứt Vỏ Cam) | vietnamtourism | 1226 | source, extension, category, difficulty, doc_id, chunk_index |

### Metadata Schema

| Trường metadata | Kiểu   | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|-----------------|--------|---------------|-------------------------------|
| `source` | `string` | `"Braised_Tofu"` | Tên gốc document — dùng để trace kết quả về file nguồn |
| `extension` | `string` | `".md"` | Loại file — hỗ trợ filter theo định dạng nếu mix `.md`/`.txt` |
| `category` | `string` | `"main_dish"`, `"seafood"`, `"dessert"` | Filter theo loại món — VD: chỉ tìm trong dessert hoặc seafood |
| `difficulty` | `string` | `"easy"`, `"medium"`, `"hard"` | Filter theo độ khó — VD: chỉ tìm món dễ nấu |
| `doc_id` | `string` | `"Orange_Fruit_Skin_Jam"` | ID gốc của document trước khi chunk — dùng để `delete_document` và group chunks cùng nguồn |
| `chunk_index` | `int` | `0`, `1`, `2`... | Vị trí chunk trong document — hỗ trợ debug và tái tạo thứ tự nội dung gốc |
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

**Loại:** FixedSizeChunker (`chunk_size=300, overlap=50`)

**Mô tả cách hoạt động:**
> `FixedSizeChunker` chia văn bản thành các đoạn có độ dài cố định tối đa 300 ký tự. Mỗi chunk liên tiếp chia sẻ 50 ký tự overlap với chunk trước đó để tránh mất ngữ cảnh tại ranh giới. Nếu văn bản ngắn hơn `chunk_size`, toàn bộ văn bản được giữ nguyên làm 1 chunk duy nhất. Bước trượt (`step = chunk_size - overlap = 250`) quyết định vị trí bắt đầu của mỗi chunk mới.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Các tài liệu công thức nấu ăn có độ dài vừa phải (1000–2500 ký tự) và nội dung phân bố đều qua các phần (Introduce, Ingredients, Process). `FixedSizeChunker` đảm bảo mỗi chunk đủ lớn để chứa 1–2 bước nấu hoàn chỉnh, đồng thời overlap 50 ký tự giữ lại phần cuối của bước trước để embedding không mất ngữ cảnh chuyển tiếp giữa các bước.

**Code snippet:**
```python
chunker = FixedSizeChunker(chunk_size=300, overlap=50)
chunks = chunker.chunk(document_text)
# Braised_Tofu.md (1208 chars) → 5 chunks, avg 282 chars
```

### So Sánh: Strategy của tôi vs Baseline

Chạy `ChunkingStrategyComparator` với `chunk_size=300, overlap=50` trên toàn bộ 5 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| `Braised_Tofu.md` | SentenceChunker (baseline tốt nhất) | 5 | 238 | Good — giữ trọn câu |
| `Braised_Tofu.md` | **FixedSizeChunker (của tôi)** | **5** | **282** | Medium — chunk lớn hơn, dễ retrieve nhưng đôi khi cắt giữa câu |
| `Duck_Porridge.md` | SentenceChunker (baseline tốt nhất) | 10 | 243 | Good |
| `Duck_Porridge.md` | **FixedSizeChunker (của tôi)** | **10** | **292** | Medium |
| `Grilled_Snails.md` | RecursiveChunker (baseline tốt nhất) | 5 | 202 | Good — tôn trọng ranh giới tự nhiên |
| `Grilled_Snails.md` | **FixedSizeChunker (của tôi)** | **4** | **291** | Medium |

**Nhận xét:** FixedSizeChunker tạo ít chunk hơn nhưng mỗi chunk lớn hơn → score retrieval trên Q1 (braised tofu) đạt `0.7012` cho chunk#2 và `0.6959` cho chunk#1, cả hai đều từ đúng document `Braised_Tofu`. Q2 (grilled snails dipping sauce) retrieve đúng `Grilled_Snails:3` với score `0.7107`. Tổng 5/5 queries đều có ít nhất 1 chunk relevant trong top-3.

### So Sánh Với Thành Viên Khác

Tất cả chạy trên cùng 5 documents, cùng embedder `all-MiniLM-L6-v2`, cùng 5 benchmark queries.

| Thành viên | Strategy | Chunks | Q1 Top-1 | Q2 Top-1 | Q3 Top-1 | Q4 Top-1 | Q5 Top-1 | Top-3 Relevant |
|-----------|----------|--------|----------|----------|----------|----------|----------|----------------|
| Tôi (Nguyễn Lê Trung) | FixedSizeChunker (300/50) | 32 | Braised_Tofu:2 (0.7012) | Grilled_Snails:3 (0.7107) ✓ | Duck_Porridge:5 (0.6558) ✓ | Orange_Fruit_Skin_Jam:4 (0.4947) △ | Savory_Pancakes:2 (0.6186) ✓ | **5/5** |
| Phạm Anh Dũng | SentenceChunker (3 sentences) | 34 | Braised_Tofu:1 (0.7493) ✓ | Grilled_Snails:2 (0.6763) ✓ | Duck_Porridge:4 (–) ✓ | Orange_Fruit_Skin_Jam:5 (0.4988) ✓ | Savory_Pancakes:1 (0.5978) ✓ | **5/5** |
| Dương Quang Đông | RecursiveChunker (300) | 39 | Braised_Tofu:3 (0.7287) ✓ | Grilled_Snails:3 (0.7001) ✓ | Duck_Porridge:5 (0.7640) ✓ | Orange_Fruit_Skin_Jam:5 (0.5260) ✓ | Savory_Pancakes:4 (0.6530) ✓ | **5/5** |
| Vương Hoàng Giang | CustomRecipeChunker (by header) | 39 | Braised_Tofu:1 (0.7420) ✓ | Grilled_Snails:5 (0.6438) △ | Duck_Porridge:5 (0.7667) ✓ | Orange_Fruit_Skin_Jam:6 (0.5260) ✓ | Savory_Pancakes:1 (0.6275) ✓ | **5/5** |

> ✓ = top-1 đúng document | △ = top-1 sai nhưng có trong top-3

**So sánh chi tiết từng strategy:**

| Strategy | Điểm mạnh | Điểm yếu |
|----------|-----------|----------|
| **FixedSizeChunker** (của tôi) | Đơn giản, nhất quán; overlap 50 giữ ngữ cảnh biên; chunk lớn dễ chứa đủ 1 bước nấu | Cắt qua ranh giới câu và section; Q4 top-1 không chứa tên món |
| **SentenceChunker** | Giữ trọn câu; Q1 top-1 chính xác nhất (0.7493) vì chunk Ingredients nguyên vẹn | Gom nhầm nội dung từ nhiều section; Q2 không lấy đúng "Step 5 Making sauce" |
| **RecursiveChunker** | Score Q3 cao nhất (0.7640); tôn trọng `\n\n` → thường giữ đúng paragraph | Tạo nhiều chunk nhỏ hơn → đôi khi phân mảnh bước nấu dài |
| **CustomRecipeChunker** | Chunk hoàn toàn khớp cấu trúc recipe; Ingredients chunk độc lập, mỗi Step là 1 unit | Q2 top-1 lấy Step 4 (grill snails) thay vì Step 5 (making sauce) vì Step 5 quá ngắn → score thấp |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> `RecursiveChunker` cho kết quả retrieval tốt nhất tổng thể — score Q3 cao nhất (0.7640), 5/5 top-1 đúng document, và tôn trọng ranh giới tự nhiên của văn bản recipe (paragraph breaks). `CustomRecipeChunker` có thiết kế lý tưởng về mặt ngữ nghĩa nhưng gặp vấn đề với các step quá ngắn (Step 5 của Grilled Snails chỉ 1 câu → chunk yếu về ngữ nghĩa embedding). `FixedSizeChunker` (strategy của tôi) vẫn đạt 5/5 nhờ overlap nhưng cần tăng `chunk_size` lên ~400 để tránh cắt giữa section quan trọng.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng `re.split(r"\. |! |\? |\.\n", text)` để tách văn bản thành danh sách câu đơn lẻ — pattern này nhận diện dấu câu kết thúc kèm khoảng trắng hoặc newline. Các câu trống sau khi strip được loại bỏ. Sau đó gom `max_sentences_per_chunk` câu liền kề thành 1 chunk bằng `" ".join(sentences[i:i+step])`, edge case văn bản rỗng hoặc không có câu nào được xử lý bằng early return `[]`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Algorithm thử lần lượt các separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Base case: nếu `len(text) <= chunk_size` thì trả về `[text]`; nếu hết separator thì force-split theo ký tự. Với mỗi separator, split văn bản thành `parts` rồi gộp dần các phần liền kề cho đến khi vượt `chunk_size` — khi đó flush chunk hiện tại và đệ quy xuống separator tiếp theo cho phần còn lại. Cách này đảm bảo chunk luôn tôn trọng ranh giới tự nhiên của văn bản ở mức cao nhất có thể.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Mỗi `Document` được embed thành vector bằng `embedding_fn(content)` và lưu vào `self._store` dưới dạng dict `{id, content, metadata, embedding}`. Khi search, query được embed cùng hàm đó rồi tính dot product với toàn bộ embedding trong store — dot product hoạt động đúng vì các vector đã được normalize (LocalEmbedder dùng `normalize_embeddings=True`). Kết quả được sort giảm dần theo score và lấy `top_k` đầu.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` filter trước bằng list comprehension — chỉ giữ lại records có metadata khớp tất cả key-value trong `metadata_filter` — sau đó chạy `_search_records` trên tập con đó. `delete_document` rebuild `self._store` bằng list comprehension loại bỏ mọi record có `metadata["doc_id"] == doc_id`, trả về `True` nếu size giảm, `False` nếu không tìm thấy.

### KnowledgeBaseAgent

**`answer`** — approach:
> Retrieve `top_k` chunks từ store bằng `store.search(question)`. Mỗi chunk được format với source label `[Source: doc_id]` rồi nối lại thành context block. Prompt được cấu trúc theo pattern: system instruction → Context block → Question → "Answer:". Kết quả trả về là dict gồm `answer` (string từ LLM) và `top_results` (list metadata của các chunk đã retrieve, gồm rank, doc_id, chunk_index, score, content_preview). Nếu không truyền `llm_fn`, agent tự dùng OpenAI `gpt-4o-mini` qua `OPENAI_API_KEY`.

### Test Results

nguye@NLT22 MINGW64 /d/2025.2/assignments/2A202600174_NguyenLeTrung_Day07 (main)
$ pytest tests/ -v
====================================================================== test session starts =======================================================================
platform win32 -- Python 3.10.11, pytest-9.0.3, pluggy-1.6.0 -- D:\2025.2\assignments\2A202600174_NguyenLeTrung_Day07\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\2025.2\assignments\2A202600174_NguyenLeTrung_Day07
plugins: anyio-4.13.0
collected 42 items                                                                                                                                                

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                       [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                         [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                          [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                               [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                               [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                     [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                      [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                    [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                      [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                      [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                 [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                             [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                       [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                              [ 35%] 
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                  [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                            [ 40%] 
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                  [ 42%] 
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                      [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                        [ 47%] 
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                          [ 50%] 
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                     [ 54%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                       [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                           [ 59%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                        [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                 [ 64%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                           [ 69%] 
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                       [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                  [ 73%] 
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                      [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                            [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                      [ 80%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                   [ 83%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                 [ 85%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                    [ 90%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                               [ 92%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                        [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                              [ 97%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                  [100%] 

======================================================================= 42 passed in 0.40s ======================================================================= 
(venv) 
nguye@NLT22 MINGW64 /d/2025.2/assignments/2A202600174_NguyenLeTrung_Day07 (main)

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Quail eggs are good for health especially for kids" | "Braised tofu with quail eggs is a Vietnamese recipe" | high | 0.5406 | Đúng (medium-high) |
| 2 | "Mix salt pepper lemon juice and sugar for the dipping sauce" | "Step 5 making sauce mix salt pepper lemon juice sugar together" | high | 0.7539 | Đúng ✓ |
| 3 | "Duck porridge is a warm dish for winter days" | "Orange fruit skin jam is a Vietnamese dessert" | low | 0.1634 | Đúng ✓ |
| 4 | "Fresh shrimps are required for savory pancakes" | "10 fresh shrimps boiled and cut in half" | high | 0.5834 | Đúng ✓ |
| 5 | "Grill the snails with fired coal until they spread their flavor" | "Boil the duck with ginger and grilled onion" | medium | 0.3742 | Đúng (medium-low) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 2 bất ngờ nhất — tuy hai câu dùng từ khác nhau ("Mix salt..." vs "Step 5 making sauce...") nhưng score đạt `0.7539` rất cao vì embedding nhận ra cùng hành động ngữ nghĩa: liệt kê nguyên liệu làm sauce. Điều này cho thấy `all-MiniLM-L6-v2` không chỉ matching từ khóa mà thực sự nắm được intent — hai câu cùng mô tả "cách làm nước chấm" nên vector gần nhau dù surface form khác. Pair 1 thấp hơn dự đoán (`0.54` thay vì `>0.7`) vì câu A nói về sức khỏe còn câu B nói về công thức — cùng từ "quail eggs" nhưng khác chủ đề chính.

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

Strategy: `FixedSizeChunker(chunk_size=300, overlap=50)` | Embedder: `all-MiniLM-L6-v2` | 32 chunks tổng

| # | Query | Top-1 Retrieved Chunk | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|----------------------|-------|-----------|------------------------|
| 1 | What ingredients are needed for braised tofu with quail eggs? | `Braised_Tofu:2` — Process steps (cắt giữa Ingredients→Process) | 0.7012 | Partial — chunk#1 (`0.6959`) mới chứa đầy đủ ingredients | Liệt kê đúng tofu, quail eggs, fish sauce, Maggi's... |
| 2 | How do you make the dipping sauce for grilled snails? | `Grilled_Snails:3` — Step 4+5+Finally | 0.7107 | **Yes ✓** — chứa "Step 5: Making sauce: Mix salt, pepper, lemon juice, sugar" | Trả lời đúng: mix salt, pepper, lemon juice, sugar + mint herb |
| 3 | What is the process for making duck porridge? | `Duck_Porridge:5` — Step 3+4 porridge process | 0.6558 | **Yes ✓** — chứa roast sticky rice + braise in broth | Mô tả đúng: boil duck, roast rice, cook in broth |
| 4 | Which dish is a dessert and how is it stored? | `Orange_Fruit_Skin_Jam:4` — Step 4 cooking process | 0.4947 | Partial — chứa "store into jar" nhưng thiếu tên món | Đề cập "store into jar and use day by day" nhưng không nêu rõ "Orange Fruit Skin Jam" |
| 5 | Which dishes require shrimp as an ingredient? | `Savory_Pancakes:2` — Ingredients list | 0.6186 | **Yes ✓** — "10 fresh shrimps... 100gr dried shrimp" | Trả lời đúng: Savory Pancakes dùng fresh shrimps và dried shrimp |

**Bao nhiêu queries trả về chunk relevant trong top-3?** **5 / 5**

> Q1 và Q4 có chunk relevant nằm ở #2 trong top-3 (không phải top-1) nhưng vẫn được retrieve thành công. Q4 là failure case đáng chú ý nhất: FixedSizeChunker cắt tên món (`Orange Fruit Skin Jam`) vào chunk trước (chunk#0) và phần lưu trữ vào chunk#4 — agent trả lời được "cách lưu" nhưng không biết tên món cụ thể. Đây là điểm yếu điển hình của fixed-size chunking: cắt qua ranh giới ngữ nghĩa quan trọng.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Kỹ năng làm việc nhóm, khả năng của vibecode trong việc phát triển sản phẩm demo trong nháy mắt.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Các bạn đã demo không chỉ kết quả mà còn có minh họa trực quan web cùng ứng dụng thực tế. Việc sử dụng top-k không chỉ trả đúng thông tin người dùng hỏi mà còn có thể gợi ý các vấn đề liên quan.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Thu thập thêm dữ liệu và thêm các kịch bản đánh giá khi tăng giảm chunk size và overlap

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10/ 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 9 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 0 / 5 |
| **Tổng** | | **82 / 100** |
