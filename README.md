# AS-AIGVTS

## 中研院科普演講影音平台現況 [[Link](https://www.youtube.com/@academiasinica4594/)]
- ✅ 知識寶庫，主題多元
- ✅ 大師雲集，內容精彩

- ⚠️ 偏好新上架或熱門影片
- ⚠️ 僅能從主題進行搜尋

- ⛔️ 沒有字幕，不夠友善
- ⛔️ 無法吸引國外人士閱聽
- ⛔️ 無法提供快速導覽
- ⛔️ 無法提供友善搜尋

## 我們的解法

- 使用 OpenAI Whisper 在地端進行語音辨識轉字幕檔
- 使用 Googletrans 進行多國語言翻譯
- 用 ChatGPT API 為影片內容撰寫摘要
- 用 Googletrans 將摘要翻譯成多國語言版本

- Google colab notebook： [[colab_notebook_AS_AIGVTS_Transcript](colab_notebook_AS_AIGVTS_Transcript)] [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AS-AIGC/AS-AIGVTS/blob/main/colab_notebook_AS_AIGVTS_Transcript)
- Python 語言版本
  - 自動產生 FAQ：[[AS-AIGFAQ.py](AS-AIGFAQ.py)]
  - 自動翻譯成多國語言版本：[[AS-AIGFAQ-to-i18n.py](AS-AIGFAQ-to-i18n.py)]
  - 產生簡易網頁：[[AS-AIGFAQ-to-HTML.py](AS-AIGFAQ-to-HTML.py)]

## 案例分享

- 【生成式 AI】Diffusion Model 原理剖析 (1/4) (optional), by 李宏毅 [[原始連結](https://www.youtube.com/watch?v=ifCDXFdeaaM)] [[加字幕後連結](https://www.youtube.com/watch?v=-_FnWFL1LLk)]
  
## 開發團隊

- 中央研究院 資訊服務處
- 中央研究院 資訊科學研究所
