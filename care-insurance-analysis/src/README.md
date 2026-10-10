# ROLE=10 再現手順（解析契約2.4）

候補 `care-S01-20261010-v3` は評価用であり、完成/暫定提出ではない。主入力S01/S02/S03/S04/S05/S06と追加参考S10のSHA256を `src/input_manifest.json` と `references/S10_excerpts.json` に照合する。原本は変更しない。C03確認済み作業コピー（SHA256 `fef7ab5b1b46bc8eb03c040c3d4767ec9aa41098c6106019397ce29623c77cf6`）を再利用し、訂正を重複適用しない。

## 実行の概要

1. Python 3.12、Node 22、`@oai/artifact-tool` 2.8.85で `src/integrate_s10.py` を実行する。S10 DOCXのSHA/サイズ、162明示セル、11表ブロック、表54/59/60合計を照合する。
2. `src/summary_v2.py` がS10の独立参考表とS01/S02の保留付き比較表を生成する。S10 R7市独自25.6日はS01の平均を復元した値と扱わず、県/全国/第1回比較を抑止する。C10・C11・C09の値と比較は保留/未算出のまま。
3. `src/summary_v2.mjs` が先頭要点1シートと印刷可能な局所注記を作り、`src/graft_v2.py` がC03作業コピーへ追加する。元14シート・148グラフと元数式/図/画像部品を保つ。
4. `src/build_candidate_v3.py` は分析要点とⅣ!J208のC04置換を固定し、`checks/candidate.json` と機械検査結果を生成する。候補SHAとcandidate_fingerprintは実ファイルから算出する。
5. `src/run_native_trial.py` で別コピーへ再計算・保存・読戻し境界試験を行う。配布候補は直接再保存しない。`fc-match`、`pdffonts`、PDF/PNGの実描画を確認し、日本語字形は読める環境でない限り未合格とする。

作業時環境ではLibreOfficeDev 26.8 alphaで候補を開きPDF化できたが、日本語TTF/OTFがなく、PDFに日本語字形が描画されなかった。日本語表示の検査は未合格。C04置換は承認済み表示例外であり、S01期間の原値復元/検証ではない。正式資料待ちのC10/C11等をS10で解除しない。
