# VSA 改善清單

> 盤點日期：2026-08-29
>
> 範圍：`src/vsa` 套件、`scripts/`、`tests/`（共 41 個 Python 檔）、封裝的 JSON 設定、CI 與打包設定，以及本機 `env/` 虛擬環境。
>
> 驗證現況（2026-08-29 更新）：核心與開發依賴已安裝並鎖定；Ruff check／format、`pip check`、44 個 unit／GUI smoke tests、實際 Qt WebChannel 互動測試，以及以 `demo_data` 執行的 `python -m vsa --smoke-test` 皆通過。

## P0：先修正確性與資源問題

- [x] 修正 ROI 圖片搜尋的參數錯誤。
  - `ui.py:277` 呼叫 `open_image_from_search(number, code, no, current_button_name)`，但 `search2.py:4` 需要 `(option, number, code, no, button_name)`。
  - 驗收：從 UI 搜尋存在／不存在的 ROI 圖片都不會拋出 `TypeError`，且錯誤會顯示在 UI。

- [x] 修正 Export Map 把「檔案名稱」建立成資料夾的問題。
  - `ui.py:199-225` 傳入的是完整 `target_file`，但 `download_file()` 對它呼叫 `os.makedirs()`。
  - 改為只建立 `Path(target_file).parent`，再 `shutil.copy2(source_file, target_file)`；若檔案已存在，明確定義覆寫或詢問行為。
  - 驗收：匯出結果是單一 `<stage>_<code>.png` 檔案，不是同名資料夾。

- [x] 修正站點名稱不一致。
  - `plot.py:34` 使用 `INN1`／`INN2`，其他 UI、JSON 與 CSV 路徑使用 `INNER1`／`INNER2`。
  - 建立唯一的 stage 常數／映射來源，避免每個模組各自寫字串。
  - 驗收：點擊 ROI 後，六個站點的對應圖片都從正確資料夾載入。

- [x] 修正 Loss Map 雙擊點位功能。
  - `lossmap_plot.py` 的 `Scattergl` 沒有設定 `customdata`，JavaScript 卻讀取 `pointData.customdata`。
  - WebGL 圖層也不會產生目前程式所查找的 `g.point` SVG 節點；應改用 Plotly 事件搭配 `QWebChannel`，並把 `No` 明確放入 `customdata`。
  - 驗收：雙擊紅／灰點都能把正確的 `No` 回填到 `PKG NO`。

- [x] 讓 Dash server 能真正停止。
  - `plot.py:178-221` 啟動背景執行緒後只 `join(timeout=1)`，沒有送出 shutdown；關閉視窗後 server 很可能仍占用 port，而且非 daemon thread 可能妨礙程式結束。
  - 使用可持有並呼叫 `shutdown()` 的 server；由 OS 配置可用 port，避免 `random.randint()` 的競爭／碰撞。
  - 驗收：反覆開關 ROI 視窗後沒有殘留 listening port，主程式可立即正常結束。

- [x] 集中管理並清除暫存檔。
  - `plot.py` 與 `lossmap_plot.py` 產生 `delete=False` HTML，離開視窗後沒有刪除。
  - `lossmap_plot.py` 改用 `TemporaryDirectory`／`try...finally`，避免例外時 `temp_dir` 未定義或清理被跳過。
  - 驗收：正常關閉與故意觸發例外後，系統暫存目錄都不持續累積 VSA HTML／CSV。

## P1：建立可重現且安全的開發環境

- [x] 補上 `pyproject.toml`（建議）或 `requirements.txt`，記錄並鎖定經驗證的直接依賴。
  - 目前程式至少使用 PySide6（含 WebEngine）、pandas、Plotly、Dash、Flask、Pillow。
  - 記錄支援的 Python 版本；目前 `env/` 是 Python 3.13.0，但只安裝了 `pip 24.2`。
  - 驗收：在全新的 `env/` 依文件安裝後，`python main.py` 可啟動，`python -m pip check` 通過。

- [x] 保留 `env/` 工作方式，但在根目錄 `.gitignore` 明確忽略虛擬環境。
  - 加入 `env/`、`.venv/`、`venv/`、`__pycache__/`、`*.py[cod]`、測試／建置 cache。
  - 現在是靠 `env/.gitignore` 自我忽略；根規則更清楚，也能防止重建環境時意外進版控。

- [x] 區分 `env/` 與 `.env`。
  - `env/` 是 Python 虛擬環境，不放進 Git。
  - `.env` 若未來用來放資料根目錄或秘密，也不放進 Git；只提交不含真實秘密的 `.env.example`。
  - 不要把 API key、帳密或內部路徑寫進 `AGENTS.md`、README、測試快照與 log。

- [x] 移除硬編碼的 `D:/Database-PC`。
  - 建立單一設定入口，例如 `VSA_DATA_ROOT` 環境變數，並提供合理預設或首次啟動選擇資料夾。
  - 用 `pathlib.Path` 組路徑，檢查解析後路徑仍位於 data root 內，避免 Lot ID／Component ID 中的 `..` 或分隔符跳出預期目錄。
  - 驗收：不改程式碼即可切換測試資料與正式資料；非法輸入會被 UI 阻擋。

- [x] 從 Git 移除產生物 `output_plot.html`，並加入忽略規則。
  - 目前該檔約 3.98 MB，執行 Customize Map 時會直接覆寫它，且多個視窗可能互相覆蓋。
  - 每個視窗改用獨立暫存檔，關閉時清除。

- [x] 新增 `README.md`。
  - 說明用途、Windows 前置需求、`env/` 建立／啟用／安裝／執行指令、資料目錄結構、必要 CSV 欄位，以及常見錯誤排查。
  - README 範例不得包含真實 lot、component、內部分享路徑或秘密。

- [x] 新增面試展示用的合成資料產生器。
  - `python -m scripts.create_demo_data` 會建立被 Git 忽略的 `demo_data/`，不需要攜帶任何正式生產資料。
  - 已用合成的 `DEMO-LOT`／`DEMO-CMP` 完成離線 Qt 啟動與 map preview smoke test。

- [x] 新增根目錄 `AGENTS.md`，讓後續 Codex／開發者遵守同一套規則。
  - 指定使用 `env\\Scripts\\python.exe` 執行測試與工具。
  - 要求正式資料目錄唯讀；測試一律使用 `tmp_path`／臨時 fixture。
  - 列出格式化、lint、測試、啟動、打包命令與完成定義。
  - 規定不得讀取、提交或輸出 `.env` 秘密；修改資料路徑／CSV schema 時必須補測試與文件。

- [x] 新增 repo-scoped Codex skill：`.agents/skills/vsa-development/`。
  - 涵蓋 VSA 修改、正式資料保護、驗證、Todo 維護，以及經使用者授權後的 commit/push 流程。
  - 已使用 `skill-creator` 內建 validator 驗證 skill 結構與 frontmatter。

## P1：補測試與自動檢查

- [x] 建立 `tests/`，先把純運算從 GUI 拆出後測試。
  - CSV schema 驗證：缺少 `No`、`Row`、`Col`、`DefectType`、空檔與型別錯誤。
  - `preprocess_csv()` 的 good／bad／flip 規則。
  - Loss Map merge：座標重複、座標缺失及 outer／inner join 的預期行為。
  - 圖片尋找：大小寫副檔名、缺圖、不同 stage 名稱。
  - 匯出：目的目錄不存在、同名檔案已存在與複製錯誤。
  - 路徑安全：空白、中文、`..`、絕對路徑與非法字元。

- [x] 擴充 CSV 與 merge edge-case 測試。
  - 驗證：`tests/test_data_processing.py` 覆蓋空檔、只有標頭、非數值座標、重複座標，以及 inner／outer 對「僅存在單一 stage 座標」的行為與未知 join 策略。
  - 補空 CSV、非數值座標、重複座標、只存在單一 stage 的座標，以及明確的 join 策略。

- [x] 加入 GUI smoke test。
  - 至少驗證主視窗可建立、產品切換會更新按鈕、初始 Product A 按鈕名稱正確，以及開關 PlotWindow 不殘留 server。
  - 測試使用 offscreen Qt 與臨時資料，不連正式 `D:/Database-PC`。

- [x] 建立 CI 與 `pyproject.toml` 工具設定。
  - 建議：Ruff（lint/format）、pytest、coverage；CI 執行 compile、lint、unit tests 與 `pip check`。
  - 先建立可接受的 baseline，再逐步收緊，避免一次格式化掩蓋功能修改。

## P2：重整架構與可維護性

- [x] 改成套件結構，例如 `src/vsa/`。
  - 驗證：`src/vsa/{config,paths,models,workers}.py` 與 `services/`、`views/`、`resources/`；單一 entry point `vsa.app:main`（`python -m vsa`）。
  - `config.py`：資料根目錄、產品與 stage 設定。
  - `paths.py`：集中建立並驗證 CSV／map／ROI／org 路徑。
  - `services/`：CSV 運算、圖片合併、檔案匯出。
  - `views/`：Qt 視窗與訊號；GUI 不直接處理 pandas 與檔案複製。
  - 保留單一 entry point，移除 `main.py` 與 `ui.py` 重複啟動程式碼。

- [x] 整併或刪除重複／未接線模組。
  - 驗證：`download.py`／`map_download.py`／`standby.py`／`defects.py`／`flip.py` 已刪除；轉換邏輯併入 `services/data.py`，`convert_csv_files()` 會實際套用 `rule.json`（`tests/test_convert.py`）。
  - `download.py` 與 `map_download.py` 完全重複。
  - 檢查 `standby.py`、`calculate_change.py`、`convert.py`、`defects.py`、`flip.py` 是否仍是正式流程的一部分。
  - `convert.py` 雖讀取 `rule.json`，實際轉換卻忽略 `rules`；預設 `user_selected_good=None` 還會造成 membership `TypeError`。

- [x] 將 `button_names.json`、`rule.json` 當作正式資源載入。
  - 驗證：`config.py` 以 `importlib.resources` 讀取並做 schema 驗證，`initUI()` 結束前呼叫一次 `update_button_names()`（`tests/test_config.py`、`tests/test_ui_smoke.py`）。
  - 不依賴目前工作目錄；使用模組位置或 package resources，明確指定 UTF-8。
  - 加 schema 驗證與清楚的 UI 錯誤，避免 JSON 壞掉後只退回空按鈕。
  - 初始化完成後立即呼叫一次按鈕更新；目前預設 Product A 仍會顯示 `Button 1...14`，直到產品選項改變。

- [x] 建立一致的資料模型與命名。
  - 驗證：`models.InspectionSelection` 統一 product／lot_id／component_id／stage；UI 文案改為一致英文，`map weight`／`map hight` 等錯字與恆真條件式已移除（ruff `F` 規則把關未使用的 import／變數）。
  - 統一 `Lot ID`、`Component ID`、`PKG NO`、product、stage 的 Python 名稱與 UI 文案。
  - 修正 `map weight`／`map hight` 等文案，決定全中文或一致的英文介面。
  - 移除永遠相同的條件式，例如 `x if stage == 'MT' else x`，以及未使用的 import／變數。

- [x] 以 logging 取代 `print()` 與廣泛的 `except Exception`。
  - 驗證：應用程式碼已無 `print()`；唯一的 `except Exception` 在 `workers.py` 的 worker 邊界，且會記錄 traceback 並回報給 UI。
  - UI 顯示可理解訊息；log 保留 traceback 與必要上下文，但不記錄秘密或大量生產 CSV 內容。
  - 捕捉具體例外；檔案不存在、CSV schema 錯誤與程式錯誤要分開處理。

- [x] 為所有外部資料做驗證與明確錯誤。
  - 驗證：`services/data.py` 在 `read_csv` 後檢查欄位與數值型別；`services/images.py` 以 context manager 開圖並把 `DecompressionBombWarning` 升級為錯誤；複製／儲存操作回傳結果路徑或拋出具體例外。
  - `pd.read_csv()` 前後驗證檔案、編碼、必要欄位與數值型別。
  - `Image.open()` 使用 context manager，處理損壞圖片與超大圖片警告。
  - 所有複製、儲存與合併操作回傳結果或拋出具體例外，不要只印出錯誤後假裝成功。

## P2：效能、穩定性與 UX

- [x] 把耗時工作移出 Qt 主執行緒。
  - 驗證：`workers.FunctionWorker` 搭配 `QThreadPool`，`MainWindow.run_background_task()` 提供忙碌游標、狀態列與錯誤對話框（`tests/test_workers.py`）。
  - CSV 載入／merge、圖片 resize／拼接、資料夾複製會讓 GUI 凍結；使用 `QThreadPool`／worker，提供進度、取消與錯誤回報。

- [x] 降低大型拼圖的記憶體尖峰。
  - 驗證：`services/images.py` 逐張開圖／縮放／貼上後關閉，並在合成前用 `estimate_canvas_bytes()` 擋下超過 512 MiB 的請求（`tests/test_image_services.py`）。
  - Vertical 圖目前約為 `15120 x 4340`，單一 RGB canvas 約 188 MiB，尚未計入 14 張 resize 後圖片與 Qt preview。
  - 逐張開啟、縮放、貼上後立即關閉；preview 使用縮圖，輸出尺寸改成可設定且先估算記憶體。

- [x] 優化 pandas／Plotly 建圖。
  - 驗證：hover 文字改為向量化字串運算（無 `iterrows()`）；`services/colors.py` 以名稱雜湊決定顏色，同一 defect 在不同檔案固定同色；百分比改用驗證後的總點數並處理除以 0；`services/plotly_assets.py` 讓每個視窗只寫一份離線 `plotly.min.js`，HTML 以相對路徑引用（`tests/test_plot_assets.py`）。
  - 避免 `iterrows()` 逐列建立 hover 資料；使用向量化字串操作。
  - 顏色映射改為固定、可重現，避免每次開啟同一 defect 顏色不同。
  - `customize_map_plot.py` 百分比不能寫死除以 `96721`；應使用驗證後的總點數／基準數，並定義分母為 0 的行為。
  - 評估 Plotly JS 重複嵌入每個 HTML 所造成的檔案大小，改成受控的共用資源或明確的離線 bundle。

- [x] 改善視窗與輸入體驗。
  - 驗證：map width／height／point size 使用 `QIntValidator` 並實際傳入 Loss Map 與 Custom Map；缺少 stage／Lot ID／Component ID 會先擋下並以 `QMessageBox` 提示；所有視窗改用 `resize()`＋最小尺寸與 size policy，不再有固定像素 `setGeometry`／`setFixedSize`（`tests/test_ui_smoke.py`）。
  - 使用 `QIntValidator`／數值範圍驗證 map width、height、point size。
  - 沒選 stage、Lot ID 或 Component ID 時先阻擋操作。
  - 所有成功／失敗／找不到檔案都用一致的 `QMessageBox` 或狀態列，不只寫 console。
  - 固定像素尺寸改為可縮放 layout，支援不同 DPI 與螢幕大小。

## P3：交付與文件化

- [x] 決定正式打包方式（例如 PyInstaller），並從乾淨 `env/` 重建驗證。
  - 驗證：`vsa.spec` 產生 one-folder bundle，本機以 `pyinstaller vsa.spec --noconfirm --clean` 重建成功，`dist/VSA/_internal/vsa/resources` 含兩個 JSON，`dist\VSA\VSA.exe --smoke-test` 以 offscreen 執行回傳 0。
  - 乾淨環境驗證：移除 editable install（重現套件未安裝、直接從 checkout build 的情境）後重新 build，resources 完整且 `VSA.exe --smoke-test` 回傳 0。CI 不執行打包，避免每次 push 多花約 5 分鐘。
- [x] 記錄資料格式版本與相容性策略，避免 CSV 欄位或 stage 改名後靜默產生錯圖。
  - 驗證：`docs/DATA_FORMAT.md` 定義 1.0 目錄／CSV 契約與相容性政策。
- [x] 若多人使用，加入版本號、變更紀錄與可回報診斷資訊（程式版本、Python／依賴版本；不含敏感資料）。
  - 驗證：`vsa.__version__` 0.2.0、`CHANGELOG.md`，以及 UI 上的 Diagnostics 按鈕（`diagnostics.py`，只輸出版本與平台）。
- [x] 補上授權／內部使用聲明、資料隱私與正式資料備份／唯讀政策。
  - 驗證：`LICENSE.md` 說明 portfolio 使用範圍、禁止納入正式資料，以及唯讀／備份責任。

## 建議執行順序

1. 所有 P0 已完成：主要功能正確性與資源洩漏已有自動化回歸測試。
2. 建立依賴檔、根 `.gitignore`、README 與 `.env.example`（若採環境變數）；`AGENTS.md` 與 repo skill 已完成。
3. 抽出路徑／CSV／圖片純函式並補 unit tests，再做套件化重構。
4. 加 CI 後處理背景 worker、效能與 UI 改善。
5. 最後建立乾淨環境的打包與發佈流程。
