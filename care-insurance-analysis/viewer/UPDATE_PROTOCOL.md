# 共有タイムライン・処理アトラス 更新規約

解析契約2.4不変。通常STATEは00専有。正本は非公開GitHub `myonmyon545-cell/-` の `care-insurance-analysis/viewer/`。計画チャットとROLE00は同じパス・同じコミットを直接読む。別チャットを起動したとは扱わない。

## 分担

| 担当 | 更新対象 | 禁止・受渡し |
|---|---|---|
| この計画チャット | 指示・会話原文/要約の区別、決定、表示構成、PLANの運用定義 | 通常STATE/10/20/30報告は変更しない |
| ROLE00 | STATE、同一コミットの保存報告から確認した進捗・候補・提出台帳、共通画面の固定入力/再生成 | 別チャット稼働を推測しない。他担当の報告を編集しない |
| ROLE10 | 実処理工程、コマンド、入出力ID版SHA、検査/失敗/時間、私有ファイル実manifest、候補に対応した最終添付 | 原本・個票・秘密はGitHubへ保存しない |
| ROLE20 | 固定候補に対するログ・添付画面・未収録・表示の独立確認 | 表示だけで計算/再現の合格を与えない |
| ROLE40 | 同じ画面と記録の閲覧 | 書込みしない |

## 更新トランザクション

1. main HEADを固定し、PLAN/STATE/10/20/30、logs/timeline、viewerの最新を同じ版で読む。
2. 各担当は固有event_idの自分のイベントをlogs/eventsへ追加。原文/要約/保存報告/予定を区別。元送信日時未取得ならnull。閲覧取得時刻を元送信時刻に転用しない。
3. 前版sourcesを保持し、未収録の新コミット/報告版/イベント/取得可能な会話を重複IDを除いて追記。巨大な生成物の再帰的差分複製は避け、固定コミット参照を残す。
4. viewer/input.jsonは固定コミットのtree一覧（GitHubで実在するもの）、PLAN、STATE、10/20/30を格納。実データ原本を埋め込まない。
5. `python tools/build_viewer.py --input viewer/input.json --timeline logs/timeline/timeline.json --template viewer/viewer_template.html --out <別の作業フォルダ>`。依存Python3/PyYAML。API接続・認証は生成器に埋め込まない。
6. JSON構造・一意ID・工程依存・日時・再生成records/ファイル一覧一致・JS構文・SHAを検査。ブラウザ検証未実施なら明記。
7. 一時出力を検証後、viewer/index.html/process_atlas.json/manifest.jsonへ反映。更新前HEADをexpected_shaとして非強制保存。競合したら現行版を再取得し他者追記を取り込んで再生成。上書き強行しない。
8. 固定保存コミットで変更ファイルを読戻し一致を確認。画面は固定スナップショット。GitHub更新だけでは既存の添付HTMLや未公開Siteは更新されない。

## 継続更新

### ROLE00の通常進捗更新

「更新」「進捗確認」などの通常依頼でも、この規約の更新トランザクション1～8を実施する。PLAN/STATE/10/20/30と決定JSON、UPDATE_PROTOCOL.md/platform.json、logs/timelineを同じmain HEADで固定する。報告本文が前回から変わらない担当は「最新状況未確認」と記録し、最終報告日時を保つ。確認時刻で報告日時を更新しない。

STATEの表示運用版・確認元・報告鮮度を更新し、00固有イベント、追加コミットと未収録イベントを既存sourcesへ重複なく追記する。通常STATEと共有表示の固定入力を同じ保存トランザクションで反映し、timelineとviewerを一時出力で再生成・検査する。viewer/platform.jsonのnormal_progress_updateに今回の入力コミットと検査結果を記録する。次回更新でこの保存コミットの履歴を取り込む。

保存後は固定コミットで全変更を読戻し、進捗の確認元と共有画面の保存版を併記する。確認したのがGitHubの固定画面だけなら、既存添付HTML・Site・自動タスクの実行も更新されたとは報告しない。解析工程の完了・候補合格は別途保存報告の根拠が必要。


両チャットの更新要求・記録保存後に上記を実施。自動タスクが有効なら同じ規約で保存された変更を確認する。このチャットの自動タスクはSTATEを書かず、表示/自分のイベントだけ更新する。00の通常更新は独立。無人の別チャット全文収集は不可能として未収録に残す。

Sites配信：非公開Site project_id `appgprj_6ac9a6f33718819199cfb04689e0550f` を使用。URLはplatform.jsonのhosting.urlが正本。同じID・owner-privateを維持し、多重作成しない。Sites skillのsource helperは `/root/.codex/plugins/cache/openai-curated-remote/sites/1.0.0/scripts/site-workflow.mjs` 。既存Siteのget_siteとcreate_source_repository_write_credentialから正規手順でsourceを開く。dist/index.htmlへviewer生成物、dist/timeline.htmlへタイムライン生成物を配置してsource同期・package・private deployを行う。成功したURL/版/deployment_idをplatform.jsonへ保存。元資料・個票・認証情報はsourceへ含めない。添付HTMLのプレビューではJavaScriptが動かない場合があるため、通常のブラウザでhosting.urlを開く。実機検証済みとは扱わない。

## 最終提出は別枠・固定版

10はT12/T08で `介護保険解析_処理工程アトラス.html` と `処理工程アトラス.json`、対応manifestを全ログZIPへ収録し、HTMLを別添ファイルとしても保存。最終候補ID/版/SHA、計画版、コードコミット、20判定、入力ハッシュ、最終ログZIP SHAを対応付ける。ZIP自己ハッシュは自身へ入れず00提出台帳で管理。

実処理一覧は担当・実日時・コマンド（秘密除外）・終了コード・入力・出力・検証状態・失敗/再試行・証拠を表示。現行計画と履歴上の旧版実績を区別。詳細フローは実際の依存/条件分岐/評価差戻しを示す。予定を実施済みノードにしない。

最終ファイルツリーは実際に提出するファイルと全ログZIP内部manifestから生成。入れ子フォルダ・ファイルの概要、担当、用途、実在状態、SHA、候補対応、関連工程、収録/未収録をクリックで表示。私有ファイルはWebへアップロードせず、ローカル添付でメタデータを表示。初期画面のGitHub実在ツリーを最終全データツリーと誤表示しない。

3D階層は奥行きを持つ配置・角度操作・階層移動を提供し、同じ情報の通常ツリーも常に使える。iPadのタップ・キーボード・オフライン動作を検証。新候補の実態とクリック概要を20がQ14の既存全ログ確認と合わせて検査。未検証・不足は完成版でも明記し、評価を代替しない。
