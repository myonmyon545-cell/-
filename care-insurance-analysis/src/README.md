# ROLE=10 再現手順（解析契約2.2）

main の候補登録コミットと `checks/candidate.json` に固定された入力・定義・コード版を参照する。元資料はプロジェクト情報源のS01～S06を使用し、SHA256を `src/input_manifest.json` と照合する。原本Excel/PDFと個票はGitHubへ格納しない。

## 保存済みの処理

1. `inspect_inputs.py` でS01/S02の14シートと元値を読取り、`prepare_contract.py` と `metric_inventory.py` で148表・3158指標を構成する。
2. `calculate.py` と `verify_extraction.py` で6316入力別値を抽出し、独立した読取りパーサーで元値を照合する。
3. ROLE=20が独立PASSとしたC03を、Artifact ToolでS01作業コピーのⅠ!G513:G521へ適用する。`preserve_package.py` で元14シート・148グラフ・元数式・描画・印刷部品を保持したまま要点シートを追加する。S01/S02原本は変更しない。
4. `apply_c03_overlay.py` はS01作業コピーとS02のⅢ件数を出所付きで集計へ反映する。
5. `apply_role30.py` は `reports/30.json` のE20-01/C10/C11/入力別状態案を元資料と照合し、定義・抽出・比較の保留を伝播する。正式根拠のない値・地域見出しは確定しない。
6. `summarize_checks.py` で全指標の入力別状態と検査を出力する。`replay_pipeline.py` が別一時出力への確認用再実行を行い、定義・抽出・状態・検査の6ファイルが一致することを確認する。
7. `build_candidate_tables.py` の全6316指標と1478比較・定義/保留表示から、`candidate_donor.mjs` がArtifact Toolで新規4シートを作成する。`graft_candidate.py` は確認済みC03コピーへ4シートを追加し、既存15シートの部品を保持する。
8. `build_candidate.py` は入力別ID・状態・比較抑止を `checks/candidate.json` に固定し、`tools/verify_handoff.py` とユニットテストで機械契約を検査する。候補の `code_commit` はこのコードと定義を固定した先行コミットを示す。

候補は20の初回全範囲独立評価対象。日本語フォントが実行環境になく、表示検査は未合格。C04/C10/C11の正式資料も未着である。保留値の数値結論を抑止し、完成/暫定提出とは区別する。
