# ROLE=10 実行・再開

計画版2.2。最初の入力版と管理情報はmainの14ad689ab195ed5c10a8ecdc01863bef4204c50dから取得。

## 確認済み

- 入力S01～S06のバイトハッシュは計画と一致。添付の別ID・別名は同じハッシュで対応付ける。
- 指示書とR5まとめ見本は同じバイト内容。R5元データは形式参照で、本文は令和4年度第2回。
- S01の元14シートと148グラフ、数式・印刷構成を確認。
- 148の表ブロック、74の調査選択表、36の重点項目詳細表の対応を定義した。これは分析合格や148指標の計算完了を意味しない。
- C03の見出し、Ⅲ内訳、Ⅰ割合、Ⅳ件数はROLE=10側で一致。独立評価前なので修正未適用。
- C04は保留。元送信・集計結果または個票の調査依頼日と実施日が必要。
- C09：Ⅲ変更率N110:N116の既存#DIV/0!は軽度変更構成比の分母J109=0による。未算出を0％に変えない。
- C10：第5群「薬の内服」H71:R73の件数と掲載割合が不一致。S01市の件数合計2848は対象1787とも一致しない。元集計と列定義が必要。
- C11：申請区分別変更率の一部は同表の対象件数を分母にすると掲載比率と不一致。除外ケースや別分母を推測しない。
- S01/S02の全章から6,316値を抽出し、別の読取りパーサーで全値の原本一致を確認。計算可能な比率2,170件、原値の丸め区間7件、件数整数性2,258件、明示された内訳合計112件を照合。provided値は転記照合だけ。
- 比較1,469件中1,422件を計算し、47件を保留。元セル97件は保留・欠損。独立評価による指標網羅性の承認は未実施。
- 計算の確認用再実行は1回行い、抽出結果・数値チェックJSONがバイト単位で一致。
- 通常のArtifact Tool全体再保存は複合グラフを保持できず不合格。候補に採用しない。
- Artifact Toolで作った新シートをパーツ保持アダプターで原本のコピーに登録する試行は、元シート・グラフ・描画・印刷・元スタイルを保持した。
- 新しい割合数式の再計算、分子変更への反応、入力復元を試した。既存キャッシュの保持と新数式の再計算は区別する。

## 未完了

- T03は表示検査待ち。日本語フォントが実行環境にないため、日本語のプレビューは不合格。確認用ブックは候補でも完成品でもない。
- 原表の必要セル変更を含む経路検査は未完了。C03の独立評価後に変更箇所を明示した保持試験が必要。
- T04/T05の抽出・計算は別ファイルに保存。候補Excel、最終Excel、候補検査JSONは未生成。新たな不整合は保留し、分析合格とは表示しない。
- M02～M04は個票CSV・正式列定義・合議体ID・認定ソフト／VBA実行環境待ち。地域集計から合議体を推定しない。

## 実行環境

PythonとNodeはCODEX_PRIMARY_RUNTIME_PYTHON、CODEX_PRIMARY_RUNTIME_NODEを使用する。
Python側の抽出・検査・保存保持アダプターは標準ライブラリ。xls通常読取りのみxlrdを使用。
Excelのシート作成は@oai/artifact-tool。通常の書込みで原ブック全体を再出力しない。

作業ディレクトリをプロジェクトルートとした実行例：

```bash
"$CODEX_PRIMARY_RUNTIME_PYTHON" care-insurance-analysis/src/inspect_inputs.py --sources /path/to/project_sources --out /path/to/work/inspection
"$CODEX_PRIMARY_RUNTIME_PYTHON" care-insurance-analysis/src/prepare_contract.py --inspection /path/to/work/inspection --out /path/to/work/contract
"$CODEX_PRIMARY_RUNTIME_PYTHON" care-insurance-analysis/src/metric_inventory.py --inspection /path/to/work/inspection --contract /path/to/work/contract
"$CODEX_PRIMARY_RUNTIME_PYTHON" care-insurance-analysis/src/calculate.py --inspection /path/to/work/inspection --contract /path/to/work/contract --out /path/to/work/calculation
"$CODEX_PRIMARY_RUNTIME_PYTHON" care-insurance-analysis/src/verify_extraction.py --sources /path/to/project_sources --calculation /path/to/work/calculation
"$CODEX_PRIMARY_RUNTIME_PYTHON" care-insurance-analysis/src/summarize_checks.py --inspection /path/to/work/inspection --contract /path/to/work/contract --calculation /path/to/work/calculation --out /path/to/work/final_checks
```

pilot.mjsはOS一時ディレクトリから起動する。その場所にランタイムのnode_modulesへのシンボリックリンクとpilot.mjsへのシンボリックリンクを置き、Nodeの--preserve-symlinks-mainを指定する。原本のローカルパスと一時出力先を引数で渡す。保存保持は以下で別検査する。

```bash
"$CODEX_PRIMARY_RUNTIME_PYTHON" care-insurance-analysis/src/preserve_package.py --source /path/to/S01 --donor /path/to/pilot.xlsx --out /path/to/preserved_pilot.xlsx --checks /path/to/preservation.json
python3 -m unittest discover -s care-insurance-analysis/tools -p 'test_*.py' -v
python3 care-insurance-analysis/tools/verify_handoff.py
```

## 次の操作

1. 日本語に対応したTTF/OTFフォントを実行環境に提供し、表示を再検査する。原本の字体や印刷設定は変更しない。
2. ROLE=20はC03の根拠を元資料から独立確認する。合格を受けるまでC03は修正候補。
3. ROLE=10は保存済みT04を再利用し、T03の表示・必要セル変更とT05の修正保留から継続する。C04/C10/C11の正式元集計を確認し、解消した影響範囲だけ再計算する。T06はT03合格とT05完了が条件。
4. ROLE=00だけがreports/10の確認結果をSTATEへ反映する。

原本Excel・PDF・個票・認証情報はGitHubへ送らない。
