# 介護保険データ解析 AI実行仕様

解析契約2.4 / 運用版2.4.3 / 2026-10-10

ROLE=00|10|20|30|40。最新ユーザー判断を優先。旧候補と報告は変更しない。全条件は以下のYAMLを正本とする。

```yaml
meta:
  schema: care_analysis_execution_v2
  revision: '2.4'
  operations_revision: 2.4.4
  operations_updated_at: '2026-10-12'
  completed_workbook_sheet_requirement: 完成ブックは従来どおり15シート必須。
  print_probe_scope_decision:
    decision: 印刷確認コピーは注記対象の3シートで構造受入とする。
    decided_at: '2026-10-12T09:32:15+09:00'
    authority: ROLE00へのユーザー明示判断
    evidence: reports/10.json task_results.T11_E20-04_unit3 の保存済み実測。印刷確認コピーは3シート、グラフ部品148件、局所注記15件、SHA一致、元コピーSHA検査前後不変。
    scope_limit: この判断は印刷確認コピーの構造範囲だけに適用。完成ブック15シート要件は変更しない。
    excluded_acceptances: 日本語実描画、全生成再実行、Excel再計算、候補評価、E20-04全体の合格を意味しない。
    next_role: '10'
    next_unit: 再現ZIP内の機械固有パス修正と手順・環境記録の収録
  version_policy: revisionは解析・評価契約、operations_revisionはその契約を変えない閲覧・案内の運用版。運用だけの変更は候補の評価を無効化しない。入力・定義・コード・テンプレート・要件・検査・受入条件への変更はrevisionを更新し、既存の再評価規則を適用する。
  project: 介護保険データ解析
  state: approved_missing_and_substitution_pending_candidate
  canonical_plan: GitHub mainのcare-insurance-analysis/PLAN.md。本ファイルは同じ版の導入用写し。GitHubを読めない場合は確定コミットの写しを使う。
  checked_at: '2026-10-10T10:24:49+09:00'
  deadline:
    date: '2026-10-12'
    timezone: Asia/Tokyo
    user_time_specified: false
  target_submission: '2026-10-12T21:00:00+09:00'
  deadline_interpretation: 三連休最終日の同日中。21時は予備時間を確保する内部目標。
  execution: one_off
  reproducibility: same_inputs_code_config_environment_produce_same_values_and_verdicts
  priorities:
  - 期限内の正確な成果
  - R5の掲載構成
  - 再現性
  - 処理速度
  execution_status_policy: 旧2.2候補v1とFAIL評価を保持。2.4はユーザー指定の置換/欠落/除外とログ契約を追加。新候補適用・評価・最終ログZIPは未実施。別チャット実行状態は観測しない。
invariants:
- S01を主対象とし、C04の調査平均表示のみユーザー承認によりS10の年度提供値25.6日へ置換。原本は変更しない。期間違いを明記し比較から除外。
- R5は形式参照。年度・期間・数値は本文で判定し、過去値を転用しない。
- 数値はコードと表計算で処理し、AIの暗算や生成文を数値の正本にしない。
- 事実、解釈、仮説、実施結果を区別する。未確認は補完しない。
- 最終Excelの書込みは10だけ、STATEの書込みは00だけ。
- 別チャットの自動操作、共有記憶、自動監視を前提にしない。
- 期限が迫っても検査を省略せず、保留・暫定と完成を区別する。
- 今回用のコードでよい。常設サイト、DB、定期実行、汎用ライブラリ、新規GitHub構築を必須にしない。
- C10欠落・C12除外・C09未算出・M未実施は承認された完了範囲。ただし未検証値を合格値にしない。C11の免除は未指示。
sources:
  S01:
    name: 処理対象データ群.xlsx
    id: libfile_2f275b2a53d481919fb7d942fbecc486
    sha256: 5721ee2b38cb8f55f973f149fe32f67dcfe5453645fcfdccdb934b169bcd2a2d
    role: target
    municipality: 三島市22206
    label: 令和7年度第2回
    application_period:
    - '2025-04-01'
    - '2025-09-30'
    warehouse_cutoff: '2025-11-30'
  S02:
    name: 第1回.xlsx相当の文字化け名ファイル
    id: libfile_49bf2650277881919afc2e41b9afaca2
    sha256: 9b29b315bf310770295e8fe60ba2953362f3cff21b3d78adfe255c42f2c26304
    role: prior_period_reference
    label: 令和7年度第1回
    application_period:
    - '2024-10-01'
    - '2025-03-31'
    warehouse_cutoff: '2025-06-30'
  S03:
    name: R5　元データ.xlsx
    id: libfile_6ef50a7e48148191bab971c64f1df614
    sha256: e4207ce1b47673fd6ec24e9184ea32a285698dcd0762bff612f01ce4f908c08f
    role: structure_and_presentation_reference
    actual_data: 令和4年度第2回、申請期間2022-04-01～2022-09-30
    user_name_binding: ユーザーのR5基データは現状この資料と解釈。別資料が明示されたら形式要件だけ更新。
  S04:
    name: 指示書
    id: libfile_348a1421657c8191938bc42e4a79b9ea
    sha256: d879ed1d222d43deb1d1f962e66e8b6d72eadac355596980e78d5ad0a49ec800
    format: docx_without_extension
    role: analysis_priorities_from_old_meeting_script
  S05:
    name: manual.pdf
    id: libfile_7a46b17eb12c8191b3104fe6a8f4f0aa
    sha256: 87d0353e8a53a432146a0e918dc1bd0ed32e8b3884dcb3cdc162994cb037c8d1
    role: board_analysis_procedure
    pages: 9
    focus: p1集計項目、p3-4CSV抽出、p5出力と件数確認
  S06:
    name: Tool_v1.3 (1).xls
    id: libfile_6f78bde68948819198a39bb69b17af54
    sha256: b74b37c05a97d053ef46c16f380177f5a0724151dac5daff1c4076290671e524
    role: board_analysis_tool
    limitation: 通常セル読取りは確認済み。VBA実行は未確認。
  S07:
    name: 介護保険データ解析_プロジェクト共通指示.md
    id: libfile_f293e5879930819186b897dc0e3c4338
    body_revision: '2.0'
  S08:
    name: プロジェクト作業計画_共通指示.md
    id: libfile_b1e28b0e61a48191b21f809be438f8f4
    body_revision: '2.0'
  S09:
    name: プロジェクト作業計画_詳細運用.md
    id: libfile_605f9fb6055481919ba3ce07b897a540
    body_revision: '2.0'
  S10:
    name: ③R8.5.31_個別業務資料（介護保険課）.docx
    id: libfile_292453196e588191a056e2f761753670
    library_version: '0'
    sha256: a8050346212a34760cfa2c8be7add995f3f59c3f9bfb6118ca7dc3cca3227bd2
    size_bytes: 584930
    pages: 82
    role: annual_context_and_user_authorized_survey_mean_display_substitute
    checked_at: '2026-10-10'
    reviewed: 全82ページ本文通読、関連表はDOCX XMLセルで照合。全ページ画像の目視は未実施。
    extracts: care-insurance-analysis/references/S10_excerpts.json
    instructions: care-insurance-analysis/references/S10_integration.md
    date_policy: ファイル名はR8.5.31だが第10節本文はR8.8.1。年度実績・予定・見出しごとの基準を記録。
  access_policy: IDを実際に解決する。読める保証はなく、添付済み実ファイルがあればそれを使う。
  version_policy: 本文版番号と保存サービスの版を区別する。ハッシュ変更時は影響工程だけ再処理。
  deduplication:
    method: bytes_sha256
    groups:
    - S01と第2回原名
    - S02とそのコピー
    - S03とそのコピー
    - 指示書と読み原稿R5①とR5まとめ見本2通
    - manualのコピー
    - Toolのコピー
    action: 一つだけ採用し、別名とIDをSTATEへ記録。削除・改名しない。
layers:
  L0: 目的・期限・一度の処理・再現性
  L1: 入力版・本文・元セル・確認結果・不足
  L2: 必須要件・成果物・完了条件
  L3: 抽出・計算・保存・独立評価の方法
  L4: 工程実行・受渡し・途中保存
  L5: 検査・修正・進捗・再開
  interpretation: 判断を整理する層。六つの別チャットや直列処理を意味しない。逐語的な内部思考は要求しない。
roles:
  '00':
    chat: 00 進捗管理パネル
    model: GPT-6 Luna
    effort: High
    writes:
    - GitHubのSTATE.json
    - 現行PLAN.md
    - 自役割の追記イベントと取得可能な公開会話/実行ログ（ログ原データは非公開保存）
    duties:
    - 版と担当の固定
    - 報告による状態更新
    - 期限への影響
    - 次の具体的操作
  '10':
    chat: 10 作業
    model: GPT-6.1 Sol
    effort: Medium
    escalate_to_high:
    - 定義の争点
    - 複雑な保存方式
    - 複雑な算出
    writes:
    - 実行コード
    - 中間結果
    - 作業コピー
    - 候補Excel
    - 最終Excel
    - 再現パッケージ
    - GitHubのreports/10.json
    - 自役割の追記イベントと取得可能な公開会話/実行ログ（ログ原データは非公開保存）
    duties:
    - 読取り
    - 抽出
    - 計算
    - 修正適用
    - 保存
  '20':
    chat: 20 評価
    model: GPT-6 Astra
    effort: High
    writes:
    - GitHubのreports/20.json
    - 自役割の追記イベントと取得可能な公開会話/実行ログ（ログ原データは非公開保存）
    duties:
    - 初回は全必須範囲を元資料から独立評価
    - 修正後は影響閉包と重要問題を再評価
    - 機械検査結果と解釈・表示・出所を別判定
    forbidden_writes:
    - Excel
    - 作業コード
    - STATE
  '30':
    chat: 30 修正
    model: GPT-6.1 Sol
    effort: Medium
    escalate_to_high: 複雑な原因。仕様争点はAstraを候補にする。
    writes:
    - GitHubのreports/30.json
    - 自役割の追記イベントと取得可能な公開会話/実行ログ（ログ原データは非公開保存）
    duties:
    - 再現例
    - 原因
    - 変更箇所
    - 根拠
    - 影響範囲
    - 再検証条件
    forbidden_writes:
    - Excel
    - STATE
  '40':
    chat: 40 作業履歴
    model: GPT-6 Luna
    effort: Medium
    access: read_only
    writes: []
    duties:
    - PLAN・STATE・10/20/30の報告を同一コミットで読む
    - 当該フォルダのコミット履歴と必要な過去版・差分から直近10件を一覧表示
    - 計画変更・解析作業・評価・修正・管理更新を区別し、細かな同一作業はまとめる
    - 確認日時・対象コミット・最新記録日時・未解決事項・次の操作を表示
    - 更新指示のたびに再取得し、前回確認からの差分を優先して表示
    forbidden_writes:
    - PLAN
    - STATE
    - 役割別報告
    - コード
    - Excel
    detail: care-insurance-analysis/roles/40.md
  model_fallbacks:
    Astra_unavailable: 別評価チャットのSol High
    Luna_unavailable: Sol Medium
  model_selection: 推奨配置。各チャットの実際の選択欄で設定し記録する。文章の名前では切り替わらない。
  transfer: GitHubの役割別報告ファイルを更新し、次担当は同じ版を取得する。ユーザーは次の工程を開始する短い指示を送る。接続できないチャットには確定版を添付。
  feedback: 10→20→00。指摘ありは20→30→10→20→00。修正は候補版を進め、同じ版の相互待ちを作らない。
requirements:
  R01:
    content: 指定対象・期間・R5形式
    tasks:
    - T01
    - T02
    - T03
    - T06
    - T07
    checks:
    - Q01
    - Q06
  R02:
    content: 人口構成・高齢化・75歳以上・85歳以上
    tasks:
    - T04
    - T05
    - T07
    checks:
    - Q01
    - Q02
    - Q03
  R03:
    content: 認定率・軽度・中重度・認定者構成
    tasks:
    - T04
    - T05
    - T07
    checks:
    - Q01
    - Q02
    - Q03
  R04:
    content: 認知症II・III以上・障害B以上
    tasks:
    - T04
    - T05
    - T07
    checks:
    - Q02
    - Q03
    - Q04
  R05:
    content: 調査5群・特別な医療・影響5項目・補正
    tasks:
    - T04
    - T05
    - T07
    checks:
    - Q01
    - Q03
    - Q05
  R06:
    content: 一次二次判定・変更率・申請区分・有効期間
    tasks:
    - T04
    - T05
    - T07
    checks:
    - Q02
    - Q03
    - Q04
  R07:
    content: 被保険者・申請件数・意見書と調査と認定期間
    tasks:
    - T04
    - T05
    - T07
    checks:
    - Q01
    - Q02
    - Q03
    - Q04
  R08:
    content: manualの仕様と合議体処理可否
    tasks:
    - T02
    - M01
    conditional:
    - M02
    - M03
    - M04
    checks:
    - Q01
    - Q02
    - Q04
  R09:
    content: 4チャット・評価修正・進捗再開
    tasks:
    - T01
    - T07
    - T08
    checks:
    - Q11
    - Q12
  R10:
    content: 数値と説明の一致・保存と利用
    tasks:
    - T06
    - T07
    - T08
    checks:
    - Q06
    - Q07
    - Q08
    - Q09
    - Q10
    - Q12
  R11:
    content: 一度の処理・速度・再現性・10月12日期限
    tasks:
    - T01
    - T03
    - T07
    - T08
    checks:
    - Q11
    - Q12
  R12:
    content: 再評価の版固定・差分範囲・安価な全数検査・単一正本
    tasks:
    - T06
    - T07
    - T08
    checks:
    - Q01
    - Q02
    - Q03
    - Q06
    - Q10
    - Q12
  R13:
    content: S10年度業務参考と承認された調査平均表示の置換。S01期間の復元と混同せず、他の保留を勝手に解除しない
    tasks:
    - T09
    - T10
    - T11
    - T07
    checks:
    - Q01
    - Q02
    - Q03
    - Q04
    - Q06
    - Q09
    - Q10
    - Q11
    - Q12
    - Q13
  R14:
    content: 取得可能な全指示/会話/作業/試験/未検証/失敗/データを追跡し、別添ログZIPと簡易確認文を同じ提出に添付
    tasks:
    - T12
    - T07
    - T08
    checks:
    - Q12
    - Q14
outputs:
  workbook:
    name: R7_介護保険データ解析結果.xlsx
    base: S01_copy
    reference: S03_structure
    preserve: 元14シートの名称、掲載項目、表、目次、印刷構成、148グラフの系列参照軸配置。許可例外はC03既修正9セル、C04表示置換と必要注記、承認欠落/未算出の局所表示。例外の前後/依存先を全記録。
    add: 先頭の分析要点1シート
    summary: 上部に重点結果、下部に比較表・算出根拠・未解決事項。同じ先頭1枚内の別枠にS10業務参考を期間・母集団・集計方法・出所付きで掲載。全15枚を維持し、第2の追加シートは作らない。 置換平均をS01第2回の行へ偽装しない。簡易確認文を同じ先頭1枚の下部に掲載。
    supplement_presentation: 調査平均の採用表示はS10 R7市独自25.6日。出所・年度・独自集計・第2回比較不可を直近表示。他のS10参考は独立枠。C10欠落/C12除外/C09未算出/M未実施を先頭簡易確認文と局所に表示。
    columns:
    - 指標ID
    - 区分
    - 期間または基準日
    - 通常または補正
    - 単位
    - 市
    - 県
    - 全国
    - 第1回参考値
    - 県差
    - 全国差
    - 提供期間差
    - 元セル
    - 判定
    writing_strategy: 元ブックのコピーへ必要箇所だけ変更。148グラフの全面再作成を初期案にしない。
    correction_policy: 正式根拠で一意の修正と、今回の明示承認C04表示置換だけ許可。置換は元値の正しさを回復した修正とは区別。
  reproducibility:
    name: 介護保険解析_再現用.zip
    minimum:
    - 実行コード
    - 固定設定
    - 入力IDとハッシュと取得方法
    - 実際の依存版と環境
    - 起動順と実行コマンド
    - 検査結果
    - 修正履歴
    - 評価対象候補と検査パッケージの対応
    - 再利用した評価の出所と影響一覧
    input_retention: 後で取得できない入力だけ非公開保管。原本の大量二重コピーを必須にしない。
    excludes:
    - 認証情報
    - 汎用フレームワーク
    - インストーラ
  out_of_scope:
  - 新規読み原稿
  - 未提供月次台帳の復元
  - 個人判定
  - 集計Excelからの合議体差推定
  - 因果断定
  - 不要な高度統計
  audit_log:
    name: 介護保険解析_全作業ログ.zip
    separate_from_workbook: true
    collection_scope:
    - 取得したユーザー指示と公開応答
    - 全版プロジェクト/PLAN/STATE/役割指示
    - 役割報告とGitHub履歴/差分
    - 入力原本・各候補・中間データ・試験データ・未検証出力・失敗生成物
    - 実行コマンド/依存版/開始終了/標準出力/標準エラー/終了コード/検査結果
    - 採否・置換前後・欠落・除外・未算出と理由
    - 最終評価・提出物のID/版/SHA256・収録台帳
    storage: 原本/個票/候補等の実バイトは非公開の既存ファイル保存先に保管しログZIPへ収録。GitHubへ原本/個票/認証情報は置かず、指示・安全な集計診断・イベント・ハッシュだけ。
    limits: 内部思考や認証情報は収録しない。未取得チャット/消失一時ファイル/読めないファイルを復元したとは扱わずmissing_manifestに理由を記す。会話原文と要約を区別。
    packaging: 同一データはSHAで一度収録し別名/版との対応を台帳に残す。大容量ならZIP分冊+全巻台帳で全体を照合。外部IDだけ残して実バイト収録済みとしない。
    candidate_binding: ログは対象候補ID/版/SHA/計画版/評価を固定。チェックの自己ハッシュを避け、最終提出コミットは00の別提出記録でログZIPのSHAと対応付け。
    summary: 介護保険解析_簡易確認.mdをZIP内と別ファイルに保存し、先頭分析要点へ同内容を掲載。決定/実施/未実施/検証結果/未収録を短く分ける。
    process_atlas:
      viewer: viewer/index.html
      protocol: viewer/UPDATE_PROTOCOL.md
      state: viewer/platform.json
      builder: tools/build_viewer.py
      scope: 既存全ログの別枠閲覧・添付。実績/計画/未検証を区別。最終添付は10が固定候補と実ファイルmanifestへ対応付ける。
      ownership: 計画チャットは指示・会話・表示、00は通常STATE/保存報告からの進捗と同じ閲覧画面を更新。10は実処理・ファイル概要、20は独立確認。
      update: 各更新要求に加え期限まで毎時の自動変更確認。別チャットを起動・直接監視しない。未公開Siteを公開済みとしない。
      tree: 3D階層と通常入れ子ツリーのクリック概要。私有原データはGitHub/Webに載せない。予定と実在を区別。
    timeline:
      viewer: logs/timeline/timeline.html
      markdown: logs/timeline/TIMELINE.md
      data: logs/timeline/timeline.json
      history_sources: logs/timeline/sources/
      manifest: logs/timeline/manifest.json
      order: 日時既知はJST昇順、日時不明は会話順。保存日と送信日を区別。
      classification: 表示原文・検索要約・実JSON報告・コミット保存を区別。
      archive_inclusion: T12/T08で全ログZIPへ同じスナップショットと収録元を添付。未収録を明示し収録件数を簡易確認文へ。
      continuing_authorization: 2026-10-10の「常に許可」により本件会話収録・タイムライン更新・既存範囲の指示組込みは再確認不要。重要制約・原本保護・共有範囲を維持。
      update: 各更新要求/役割報告保存時に取得範囲を追加して再構築。無人監視/他チャット全文取得を保証しない。
value_schema:
  fields:
  - 指標ID
  - 項目カテゴリ
  - 地域
  - 期間基準日
  - 日付基準
  - 母集団
  - 通常補正区分
  - 単位
  - 分子
  - 分母
  - 値
  - 数式
  - 保存値
  - 表示桁
  - 入力ID
  - 入力ハッシュ
  - シート
  - セル
  - 有効件数
  - 根拠
  - 状態
  states:
  - valid
  - missing
  - not_applicable
  - held
  - approved_missing
  - approved_excluded
  - not_computable
  - provided_substitute
  mapping: 見出し・結合セルで同定。補助セルと隠し領域を区別し、ⅠとⅢの重複値を二重集計しない。
calculation_rules:
  population:
    aging_rate: 65歳以上人口/総人口
    age75_share: 75歳以上人口/65歳以上人口
    age85_share: 85歳以上人口/65歳以上人口
    certification_rate: 第1号認定者数/65歳以上人口
    light_rate: (要支援1+要支援2+要介護1の認定者数)/65歳以上人口
    moderate_severe_rate: (要介護2～5の認定者数)/65歳以上人口
    certification_composition: 当該区分認定者数/第1号認定者数
    stock_basis: S01とS02は同じ2025年1月基準。期間ケース1787と別母集団、合算しない。
    fixture: Ⅰ基礎情報!F261/F260 = 5125/32297 = 0.15868346905285322
  independence:
    dementia_II_plus: (IIa+IIb+IIIa+IIIb+IV+M)/当該自立度全体
    dementia_III_plus: (IIIa+IIIb+IV+M)/当該自立度全体
    evidence: 元表の集約欄と内訳に一致。S03でM=1を含む合計も一致。臨床的な順序尺度とは解釈しない。
    disability_B_plus: (B1+B2+C1+C2)/当該自立度全体
  survey:
    choice_rate: 選択件数/当該項目の有効件数
    multiple_choice: 100%に無理に合わせない。
    group_scores: 提供済み集計得点を比較。個票と公式採点規則なしに再採点しない。
    five_focus:
    - 1-1麻痺の下肢左右
    - 1-5座位保持
    - 2-1移乗
    - 2-2移動
    - 3-4短期記憶
    evidence: S01のⅡ調査項目データ（第１群）!N87:N88と詳細表。左右は個別表でも5項目の原定義を保つ。
  decisions:
    composition: 判定件数/判定結果の有効ケース数
    severe_change_rate: 重度変更数/同じ表の対象件数
    mild_change_rate: 軽度変更数/同じ表の対象件数
    change_composition: 区分からの変更数/全重度変更数または全軽度変更数
    within_category_rate: 区分からの変更数/当該一次判定区分件数
    application_category_rate: 当該申請区分変更数/同区分対象件数
    comparison_rank:
      非該当: 0
      要支援1: 1
      要支援2: 2
      要介護1: 2
      要介護2: 3
      要介護3: 4
      要介護4: 5
      要介護5: 6
    exception: 要支援2と要介護1の相互変更は変化なし。この順位を平均介護度へ使わない。
    prohibition: 一次・二次の周辺集計だけから移行表や変更件数を復元しない。ケースを住民実人数へ言い換えない。
    fixture: 84/1787 = 0.047006155567991044
  validity_months:
    formula: 開始日が1日なら開始年月、それ以外なら翌月を起点とし、終了年月-起点年月+1
    bins:
    - 1-6
    - 7-12
    - 13-24
    - 25-36
    - 37-48
    exceptions: 欠損・逆転・0月・48月超は元仕様確認。最後の区分へ押し込まない。
    fixtures:
    - 2017-04-01～2017-09-30 = 6月
    - 2017-04-15～2017-09-30 = 5月
  office_days:
    opinion: 入手日-意見書依頼日
    survey: 調査実施日-調査依頼日
    recognition: 判定日-申請日
    mean: 当該指標有効日数の総和/当該指標有効件数
    denominator: ⅣのJ189・J207・J225等を指標別に使う。県・全国の件数は異なる。
    exclusions: 判定日を越える依頼・入手・実施日と、判定日を越える申請日を元仕様に従い除外。
    allowed_cases: 同日、申請日前の依頼等は元仕様で許される場合がある。一律除外しない。
    raw_schema_needed: 欠損・終了前開始等の扱いは個票と正式仕様で固定。
    aggregate_only: 提供平均の転記・整合確認まで。個票なしに平均再計算や30日超比率を実施済みとしない。
    authorized_survey_substitution:
      decision: S10のR7調査平均25.6日へ成果物表示を置換
      status: approved_substitution_pending_application
      source: S10-09/table62/R7/survey
      period: 令和7年度・市独自年度集計
      kind: provided
      value: 25.6
      unit: 日
      original_input_unchanged: true
      raw_S01_value: 0.023503077783995522
      raw_S01_ref: Ⅳ事務データ!J208
      comparisons_allowed: false
      note: 第2回集計の復元ではない。有効n・日付定義は未確認。旧県/全国/第1回値と比較しない。
  adjustments:
    age_general_form: sum(national_age_weight * city_age_specific_value)
    validity_weight: 有効期間月数/12
    weighted_rate_general_form: sum(weight * target_flag)/sum(weight)
    policy: 適用母集団・年齢区分・重み・補正順・欠損処理が不明なら提供値を採用。創作しない。
    comparability: 通常値と補正値は別行。同じ条件だけ比較。未掲載の県補正値を作らない。
    national: 対象自治体の全ケースからの値。自治体率の単純平均にしない。掲載四分位数は元分布なしに再算出済みとしない。
  differences:
    rate_pp: 100*(city_ratio-reference_ratio)
    percent_inputs: 既に百分率の値なら二重に100倍しない。
    days: city_mean-reference_mean
    relative_percent_optional: 100*(current-prior)/prior; prior=0なら未算出
    combined_rate_optional: sum(numerator)/sum(denominator)
    combined_mean_optional: sum(mean*indicator_valid_n)/sum(indicator_valid_n)
    period_label: 提供期間差。前年比ではない。両期間の合算は2024-10～2025-09でR7通年ではない。
    full_year_aggregation_required: false
  precision:
    internal: 原数値の精度を保持し最後に丸める。表示は原則割合・日数小数1桁。
    zero_denominator: 未算出。欠損と0を区別し、IFERRORで異常を0へ隠さない。
  supplemental_context:
    source: S10
    policy: 原則年度参考。ただしC04調査平均表示のみ明示承認によりS10 R7値25.6日へ置換。他のS01/S02の値/分母/定義を置換しない。
    count_checks: 表54直営+委託、表59審査結果8区分、表60年度末7区分の整数合計を検査。嘱託/再掲を重複加算しない。
    office_days: S10のR7調査25.6日を年度独自提供値の置換表示として採用。認定47.0/意見書17.5は年度参考。有効n・日付定義未確定のためS01/S02/県全国との比較や因果説明は不可。
    stock: 年度末R7計5327は第1号/第2号範囲未確定。S01の2025年1月第1号5125やケース1787と同一扱いしない。対応人口なしで認定率を作らない。
    delay_notifications: 再掲・重複規則とR7合計が未確定。構成比/申請実人数/当期30日超率を復元しない。S10空欄と－はmissing、0扱いしない。
    ratios: S10の掲載％は原単位を記録。機械ratioへ入れるなら100で割り、表示と差分で二重100倍しない。対全申請の委託割合と訪問件数分母を混同しない。
    future: R8～R10委託計画/予算は予定の参考でありR7実績や改善効果ではない。
    validity: S10資料記載の区分別認定有効期間は背景確認。S01実月数の起算/区分集計を改変せず、異常例は正式定義確認。
known_issues:
  C01:
    observation: R5名だが本文R4、主対象R7
    action: 形式と現行期間を分ける
  C02:
    observation: manualは個票CSV、S01は地域集計
    action: M工程を条件付きにし主経路から切り離す
  C03:
    observation: Ⅰ基礎情報!G521=66、Ⅲ審査判定データ（一次・二次判定）!G136=1787。Ⅰ!G513:G520も件数と割合が不整合。
    repair_candidate: 同ブックⅢ!G128:G136から、見出しを照合してⅠ!G513:G521を復元
    proof_required: Ⅲ内訳・Ⅰ割合・Ⅳ件数を10と20が独立照合して一致。一意の根拠と修正履歴を残す。
    forbidden: 66を分母にする、Ⅲの値を都合よく変更する、未検証の原本修正
  C04:
    observation: S01のⅣ!J208=0.023503077783995522日、S02は0日
    status: approved_provided_substitute_pending_application
    resolve: 追加資料S10-09のR7調査25.6日を掲載値に置換。元S01/S02値は監査保存。元期間の復元・再算出としては未解決だが承認範囲では新資料待ちを完了障害にしない。
    withheld: 異なる期間/母集団の県全国第1回との差、旧分布と置換平均の一体表示、原因説明
    forbidden: S10年度25.6日をS01第2回平均として表示。置換平均で旧分布/中央値/四分位/有効nを復元。
  C05:
    observation: 原稿の7.4%を9.6%と8.5%より高いと説明
    action: 現行値と符号で書き直す。職員事情・コロナ等の過去の原因を流用しない
  C06:
    observation: 原稿の申請から調査と表の調査依頼から実施が異なる
    action: 表の定義を採用
  C07:
    observation: 両期間の人口認定者基準が同じ
    action: ストックを合算しない
  C08:
    observation: 速度・一回性と再現性が同時要件
    action: 今回用コードと記録を保存し一度の確認用再実行。常設化しない
  C09:
    observation: S01軽度変更数0、対応構成比7セルが0/0
    action: 既知の分母0未算出。新資料待ちや0%にしない。原エラーと未算出注記を区別。
  C10:
    observation: 薬の内服P70破損見出し、S01/S02各18数値と対応chart78
    status: approved_missing
    resolve: 元値は監査に保存。採用値null、完成物は欠落と表示。調査/復旧を本体の停止条件にしない。
  C11:
    observation: S01 14率・S02 16率の正式分母未確定。ゼロ分子3率も含む。
    status: held
    resolve: 正式対象・除外定義と申請区分別元集計。S10の年度審査内訳で復元しない。
    action: 正式分母不明の保留は維持。今回ユーザーの番号3判断なし。免除/欠落許容が明示されるまでは重要未解決として扱う。
  C12:
    observation: S10表61のR7延期理由和4417、掲載計3393。再掲424を仮に除いても3993で600差。
    status: approved_excluded
    action: 原表の数字と矛盾をログ保存し解析対象外。照会/復旧を停止条件にしない。
  C13:
    observation: S10表62のR7日数は市独自集計で公表後差替予定、定義/有効n不明。R6調査8.6は括弧付き。
    status: reference_only
    action: S03見本のⅣに日数欄があるため日数情報は残す。C04表示はS10 25.6日へ置換、期間/独自集計を明示。他の年度日数は任意参考。R7県全国/事務処理日数/30日以内率は欠落。
  C14:
    observation: S10表54 R8委託予定2920と表55 2600+324=2924に4件差。
    status: held_optional_future_plan
    action: 最新提供資料S10と市公式資料を照合。今回検索で2920/2924の正式訂正値は確定できず。任意予定参考の不一致として注記または欠落にし、本体を止めない。
  pilot:
    checks: 10
    pass: 9
    fail: 1
    failed: ⅠとⅢの一次判定合計
    scope: 全ブック検査ではない
  unavailable_from_aggregates:
  - 変更根拠項目ランキング
  - 特記事項内容
  - 月次申請台帳
  - 原稿の因果説明
manual_branch:
  dependency_of_main_path: false
  current_input: 個票CSVは現在の対象群で未確認
  conditions:
  - CSV現物
  - 合議体ID
  - 正式列定義
  - 文字コード日付形式重複規則
  - 認定ソフト権限または提供済みCSV
  - 検証済み実行環境
  tasks:
    M01:
      work: manual項目・抽出条件・入力と環境の確認
      state: 文書確認済み_実行条件未確認
    M02:
      deps:
      - M01
      work: 履歴管理の検索条件を固定してCSV抽出、選択件数と出力件数を照合
      state: 入力環境待ち
    M03:
      deps:
      - M02
      work: Toolで合議体別集計
      state: 条件待ち
    M04:
      deps:
      - M03
      work: 全合議体の出力・内訳・合計・抽出件数と例外の照合
      state: 条件待ち
  indicators:
  - 申請区分
  - 一次二次判定
  - 新規更新変更
  - 居宅施設
  - 認知症II以上
  - 自立度
  - 変更率
  - 前回更新判定
  - 支援2介護1振分け
  time_basis: manual抽出例は二次判定日、S01は申請日。母集団を揃えた範囲だけ件数照合。
  board_context: S10には12合議体・委員60人・4人/合議体。IDと個票CSVはなくM02-M04条件待ちを維持。12×4と60の意味を混同しない。
  board_limit: 1ファイル20合議体、21以上は複数出力。全出力が揃うまで完了にしない。
  execution_policy: 古いExcel設定を現環境で実施済みとしない。xls読取りや変換はVBA実行とは異なる。
  alternative: 正式定義と代表CSVによる既存出力との一致を検証した場合だけ代替実装。合議体を推測しない。
  deadline_gate: 個票CSV/正式列定義等が未提供ならM未実施を明記し本体継続。提供された場合だけ条件を確認し実行。
execution:
  T01:
    owner: '10'
    deps: []
    work: 入力ID別名期間版ハッシュ固定
    output: STATE入力台帳
    checks:
    - Q01
  T02:
    owner: '10'
    deps:
    - T01
    work: 定義母集団セル対応と既知問題固定
    output: 指標対応と保留範囲
    checks:
    - Q01
    - Q04
    - Q05
  T03:
    owner: '10'
    deps:
    - T01
    work: 分析要点追加と必要セル変更を代表に出力保持保存試行
    output: 14シート148グラフ数式印刷を保つ経路
    checks:
    - Q06
    - Q07
    - Q08
    - Q09
    - Q12
  T04:
    owner: '10'
    deps:
    - T02
    work: 全章の表と通常補正値を元セル付き抽出
    output: 構造化結果
    checks:
    - Q01
    - Q02
  T05:
    owner: '10'
    deps:
    - T04
    work: 比較と根拠付き修正を計算
    output: 比較結果と修正前後
    checks:
    - Q02
    - Q03
    - Q04
    - Q05
  T06:
    owner: '10'
    deps:
    - T03
    - T05
    - T11
    work: 保存済み30修正案とS10、今回の承認決定を一括適用。C03二重適用なし。新候補版2以上を生成固定保存。
    output: 候補ExcelのID版ハッシュとcare_candidate/v1検査パッケージを固定。reports/10と同じコミットで登録。
    checks:
    - Q06
    - Q07
    - Q08
    - Q09
    - Q10
  T07:
    owner: '20'
    deps:
    - T06
    - T12
    work: 初回は全範囲の独立評価。修正後は再評価プロセスに従い、全数機械検査＋影響閉包の独立評価。
    output: 問題IDと判定
    checks:
    - Q01
    - Q02
    - Q03
    - Q04
    - Q05
    - Q06
    - Q07
    - Q08
    - Q09
    - Q10
    - Q11
    - Q12
    - Q13
    - Q14
  T08:
    owner: '10'
    deps:
    - T07
    work: 20評価に応じて完成または暫定を保存。全作業ログに評価/修正/提出記録を追記し、Excel・再現ZIP・別添全ログZIP・簡易確認文を同時提出。
    output: Excelと再現ZIPと00への報告
    checks:
    - Q12
    - Q14
  T09:
    owner: '10'
    deps: []
    work: S10実バイトSHA・文書版・表セル・年度見出しを再確認し、11根拠ブロックを入力台帳に固定
    output: 入力台帳と実照合結果。references/S10_excerpts.jsonは計画担当の抽出根拠であり10適用済みの証明ではない。
    checks:
    - Q01
    - Q02
    - Q12
    - Q13
  T10:
    owner: '10'
    deps:
    - T09
    work: 承認決定に従いC04提供値置換・C10欠落・C12除外・C09未算出を仕分け。C11保留は維持。C13期間差/C14予定差を表示。
    output: S10-*ID別の構造化参考値・局所制約・依存表。個票と対応分母を創作しない。
    checks:
    - Q01
    - Q02
    - Q03
    - Q04
    - Q10
    - Q13
  T11:
    owner: '10'
    deps:
    - T10
    work: 先頭要点1枚に集約し年度日数置換と簡易確認文を掲載。元表/グラフ/画像の局所注記、保持/印刷/日本語/再現を同じ候補で検証。
    output: 補完が識別可能な単一要点シート、再現ZIP内の抽出根拠/再現手順/環境/検査記録
    checks:
    - Q06
    - Q07
    - Q08
    - Q09
    - Q10
    - Q11
    - Q12
    - Q13
  split: Ⅰ、Ⅱ、Ⅲ・Ⅳの3処理単位。共通抽出器を使い、章別チャットを増やさない。
  order_optimization: 説明重点のⅠ・Ⅲ・Ⅳを先に、Ⅱは一括抽出。全章の必須範囲を落とさない。
  concurrency: T02とT03は独立範囲なら並行可。同一出力への書込みは直列。
  live_estimate: 未処理単位数×実測単位時間＋生成評価保存受渡し時間の幅。確認待ちは別扱い。
  critical_path_parallel: max(t01+t02+t04+t05,t01+t03,t09+t10+t11)+t06+t12+t07+t08。依存起点と実際の並行可否を反映。
  current_remaining_path: max(追加根拠/承認仕分け,保存済み30修正と日本語環境)+候補生成保存+ログ集約+20全独立評価+修正再評価+最終ログ提出。C11は別途保留。
  optimize_current: 新チャットや30再提案を必須にせず10が一括適用。出所不変の抽出結果は再利用可。旧2.2/2.3の評価PASSは2.4へコピー不可。
  critical_path_policy: 実際に並行できない部分は加算し、修正・確認待ちも加える。残り暦時間を全て稼働時間にしない。
  T12:
    owner: '10'
    deps:
    - T06
    work: 各担当の追記ログを集約し、取得可能な全実データ・指示・履歴・失敗・未検証も非公開ログZIPに収録。未収録台帳と簡易確認文を作り候補へ対応付け。
    output: 評価前ログZIP/簡易確認文/収録ハッシュ台帳。T08で20/30/00の最終記録を追加して最終版を固定。
    checks:
    - Q12
    - Q14
milestones:
  dates:
  - target: '2026-10-09T18:00:00+09:00'
    done:
    - T01
    - T02
    - T03
    gate: 出力保持経路、C03照合、C04承認置換、C11正式分母、CSV可否
  - target: '2026-10-10T20:00:00+09:00'
    done:
    - T04
    - T05
    - T06
    gate: 全章必須範囲と既存30修正・S10参考補完を統合した新候補。v1は保存済みFAILでありこの目標の合格ではない。
  - target: '2026-10-11T20:00:00+09:00'
    done:
    - T07
    gate: 独立評価と重要修正再評価
  - target: '2026-10-12T12:00:00+09:00'
    done:
    - Q11
    - Q09
    gate: 数値仕様固定。以後は重大誤り修正と提出のみ
  - target: '2026-10-12T21:00:00+09:00'
    done:
    - T08
    gate: 保存提出。未解決なら暫定と明示
  interpretation: 逆算した内部目標。実測時間や自動実行予定ではない。
  delay_cuts:
  - 装飾
  - 新規読み原稿
  - 追加統計
  - 合議体の追加実装
  - 新しい外部連携
  never_cut:
  - 指定全章
  - R5形式
  - 計算根拠
  - 独立評価
  - 再現記録
  gate: C04/C10/C12は今回の承認範囲では新資料待ちにしない。C11正式分母と出力保持/日本語/Excel全再現/ログ収録/独立評価を確認。
checks:
  Q01: 全指標の値単位期間母集団補正条件元セルを照合。
  Q02: 整数件数と内訳は完全一致。非整数の件数を検出。
  Q03: 原内部値で再計算できる比率は絶対差1e-10を初期目安。表示値だけなら丸め区間を使う。
  Q04: 分母0、欠損、M、支援2介護1相互、月数境界、同日を代表検査。C03の原不整合を検出。
  Q05: 補正の出所条件を確認。個票なしなら転記整合検査と表示し、再算出としない。
  Q06: 元14シート・148グラフの系列参照軸配置、目次、印刷改ページ注記隠し領域を照合。数だけの一致では不十分。
  Q07: 意図しない数式エラー・循環・壊れた参照・文字化け・欠落を検出。
  Q08: 変更数式の実際の再計算後に再読取り。既存キャッシュだけで再計算済みとしない。未変更部分は保存保持を検査。
  Q09: 分析要点と変更箇所を描画。全体再出力なら全シート、限定更新なら影響範囲と原パーツ保持を確認。
  Q10: 数値と高低増減の説明、符号、分母、単位が一致。因果は根拠がある範囲。
  Q11: 同じ入力コード設定依存版で一度確認用再実行し、別一時出力の指標値判定と構成を比較。整数判定は完全一致、比率はQ03。時刻等によるファイルハッシュ差は許容。
  Q12: 開けること・保存成功・入力出力版・成果の実態を確認。未実施と未確認を合格に混ぜない。
  Q13: S10全11根拠の元表独立照合とC04 25.6日置換の年度/独自集計/出所・比較不可表示。C10欠落/C12除外/C09未算出の承認記録と局所注記、C11未免除を確認。C14を確認済訂正値と偽らない。
  finding_schema:
  - 問題ID
  - 重大度
  - 要件ID
  - 対象セルと版
  - 観測値
  - 規則
  - 再現手順
  - 影響
  - 再検証条件
  verdicts:
  - PASS
  - FAIL
  - HELD
  independence: 20は10の合格宣言を根拠にせず元資料を独立確認。機械検査のPASSだけでは完成を判定しない。
  Q14: 実データ収録台帳のSHA/サイズ/版/検証状態を照合。入力・旧候補・全試験/失敗/未検証・指示/対話の取得可能範囲を突合。未収録と要約を区別。別添ZIP保存/再開封/CRCと全収録SHA、簡易確認文と完成物の一致を20が独立検査。
release_gates:
  final: 改訂必須掲載/計算/表示/再現/保存/ログが独立評価合格し、承認範囲外の重要未解決なし。C04提供値置換/C10欠落/C12除外/C09未算出/M未実施を明示した完成は許容。C11は免除されていない。
  provisional: 読めること・原本保持・候補の整合性と既知状態表示は検査済みだが重要未確認が残る。暫定と表示し保留値の結論を抑止。
  failed_integrity: 開けない、参照破損、意図しない変更等なら最終反映を止め、診断と保存済みの確認可能部分を報告。
  deadline_policy: 期限までに承認済欠落を埋める必要なし。ただしC11や表示/整合性/再現等の未解決を自動免除しない。
  manual_status: M未実施は別欄に明示。本体を止めないが、合議体が必須と追加指示されたらその完了条件を更新。
state_and_handoff:
  canonical: GitHub PLAN1・STATE1、成果Excel1・再現ZIP1。導入用写しやZIP内の控えを独立更新しない。
  state_fields:
  - revision
  - 更新時刻
  - 入力台帳
  - 工程担当状態
  - 完了単位と対象単位
  - 候補版ハッシュ
  - 評価
  - 指標対応
  - 疑義
  - 修正根拠
  - 実測時間
  - 期限影響
  - 中間保存先
  - 停止再開条件
  - 次の操作
  statuses:
  - 未着手
  - 実行中
  - 検証待ち
  - 完了
  - 停止
  wait_reasons:
  - 先行工程
  - 入力
  - 環境
  - 回答
  panel_columns:
  - 工程
  - 担当
  - 状態と待ち理由
  - 確認済み出力
  - 評価
  - 次の操作
  progress: 保存済みシート数・指標数・必須検査件数。根拠のない完了百分率を作らない。
  report_fields:
  - 計画版
  - 工程ID
  - ROLE
  - 参照コミット
  - 入力ID版ハッシュ
  - 出力ID版ハッシュ
  - 操作検査結果
  - 問題ID影響
  - 次の担当操作
  - 再開条件
  packet_policy: 実行パッケージは現在の保存先へ。同じパスのchecks/candidate.jsonへ集計指標と検査用メタデータを更新し、10の報告と同じコミットで渡す。版履歴はGitHubと既存の保存先を使う。個票は送らない。
  single_writer: 00のみSTATEを更新。00不在なら他担当は自分の報告を保存し後で統合する。
  candidate_freeze: 評価中は版とハッシュを固定し上書きしない。修正は新しい候補版。
  persistence: 必要な節目を永続保存。同じIDの版履歴を使い、最終2等を増やさない。
  state_snapshot_in_zip: 管理情報の控えであり別の更新正本にしない。
  audit_policy: 各担当が作業/試行/失敗/未検証のイベントを役割別に保存。00だけ通常STATE更新、10だけ候補/ログZIP生成、20は独立検査、30は修正根拠、40は閲覧。過去会話全件の自動取得を保証しない。
failure_policy:
  repeat: 同じ条件の同じ失敗2回で原因確認または条件変更。無益な再試行を続けない。
  stall: 実測通常単位の3倍で出力ログ変化なしを調査開始目安。観測不能なら時間だけで停止を断定しない。
  changes:
    input_problem: 影響指標を保留、独立作業は継続。
    lost_charts: 出力試行を不合格。対応可能な限定更新経路へ切替し同じ保持検査。
    missing_csv_or_vba: Mを条件待ち、本体継続。
    long_call: 小さな単位と完了単位から再開。
    unclear_save: 保存先の現状確認。二重作成しない。
  restart: 最新計画STATE入力ハッシュと保存済み結果を確認。原因・影響・版・次の操作を残し、無変更の完了工程をやり直さない。
external_resources:
  verified_on: '2026-10-08'
  connected_verified:
  - GitHub installed/enabled、対象repo private・push可
  - Google Drive installed/enabled
  - Airtable installed/enabled
  adopted:
    GitHub: PLAN・STATE・役割別報告・実行コード・集計検査JSONの共有。確定コミットを直接読む。
    GitHub_Actions: 更新時と手動起動の軽量検査。数値の正本やAI実行主体にしない。contents:read、5分上限、追加APIキーなし、定期起動なし。
    Python_standard_library: 件数・分母・比率・版固定の高速検査と影響閉包。クラウド検査が使えなくても同じコマンドで続行。
  conditional:
    Google_Drive: 候補Excelを実際に開けないチャットが出た場合の共有候補。準備が読取り問題を解消することを確認し、使用するならExcelの正本を一つに切り替える。原本・台帳の常時複製はしない。
    Airtable: 今回の4担当と指摘JSONには導入しない。大量の指摘を絞り込む具体的障害が出たときだけ検討し、導入時間も比較。
    other_plugins: 認定ソフト・CSV・VBAの障害を実際に解消できる候補のみ検索。新しい連携の準備で期限を消費しない。
  not_adopted:
  - 常設Sites/DB
  - 通知やカレンダー自動化
  - Slack/Teamsへの送信
  - 複数サービスへの同一進捗台帳
  selection_rule: 純短縮時間=従来の再評価時間-導入と運用と失敗復旧を含む新方式時間。未計測なら短縮率を断定せず最初の評価で実測する。
  unverified:
  - 新規Excel出力の保持
  - ExcelVBA
  - 別チャットでのGitHubアクセス
  - 認定ソフトからのCSV抽出
  restrictions: 対象repoの非公開性を保つ。原本Excel/PDF、個票、認証情報はGitHubに登録しない。集計値も同意された非公開の受渡し目的だけで使用。
github_handoff:
  status: registered_on_main
  repository: myonmyon545-cell/-
  visibility: private
  branch: main
  folder: care-insurance-analysis
  url: https://github.com/myonmyon545-cell/-/tree/main/care-insurance-analysis
  authorization: 2026-10-08、ユーザーが提示済み宛先と共有内容を許可。Codexへの書込みも追認。
  paths:
    plan: care-insurance-analysis/PLAN.md
    state: care-insurance-analysis/STATE.json
    work_report: care-insurance-analysis/reports/10.json
    evaluation: care-insurance-analysis/reports/20.json
    correction: care-insurance-analysis/reports/30.json
    history_view: care-insurance-analysis/roles/40.md
    source_supplement: care-insurance-analysis/references/S10_excerpts.json
    supplement_instructions: care-insurance-analysis/references/S10_integration.md
    future_analysis_code: care-insurance-analysis/src/
    verifier: care-insurance-analysis/tools/verify_handoff.py
    candidate_checks: care-insurance-analysis/checks/candidate.json
    workflow: .github/workflows/care-handoff-check.yml
  startup_read: branchの現在コミットを取得し、PLAN・STATE・必要な報告を同じコミットで直接読む。検索インデックスを待たない。参照コミットを報告に記録。
  write_policy: 00はPLAN/STATE、10はsrc・candidate検査JSON・reports/10、20/30は自分の報告を更新。40は読取り専用。ユーザーから本件の追加指示を受けた計画担当は承認された範囲でPLAN/README/役割の運用定義を更新できるが、STATEと実行報告は各担当の専有を維持する。更新前に現在HEADとファイルSHAを読み、比較交換で競合を検出。強制上書きしない。解析契約revisionを変えるPLAN更新は00が関連STATE/報告の版と再評価状態を整合させ、一つのコミットで反映する。2026-10-10の明示依頼に限り計画担当はPLANとSTATE計画変更・保存済み報告の状態整合を同時更新できる。STATE.writer=00と通常の00専有を維持し、plan_changeの実更新担当/根拠を記録。他担当の報告、候補検査JSON、旧評価版を付け替えない。operations_revisionだけの変更ではSTATE/実行報告/候補の版を付け替えない。
  candidate_atomic_update: checks/candidate.jsonとreports/10.jsonは一つのコミットで更新。20は候補ID版SHAとcandidate_fingerprintを報告へ固定。STATE更新は00が後で統合してよい。
  capability_gate: 各役割チャットの初回に直接読取りを試す。接続できなければ確定版の添付へ切替し、00がGitHub正本へ反映。
  runner_limit: ActionsはJSON/コードの検査を実行する。別チャットを起動・遠隔操作・常時監視しない。候補Excel・元資料をActionsから取得する機能は作らない。
  activation_verification: 登録コミットのPLAN・STATE・検査ファイルを読戻し、内容のSHAを比較してから共有開始を報告。Actions実行の成否は実行結果を別途確認。
  fallback: Actionsが起動しない/枠不足/権限不足なら10が同じPython検査を実行し、版付きの結果を報告。機械検査を省略しない。
startup:
  '00': viewer/UPDATE_PROTOCOL.mdとplatform.jsonも同じコミットで読み、共有表示を更新。通常STATEは専有のまま。同一コミットのPLAN/STATE/10/20/30/決定JSONを読み、T/M/C01-C14と品質問題、期限と次操作を表示。承認範囲と未実施を分離し通常STATEを単独更新。
  '10': 現在HEADのPLAN/STATE/10/20/30、references/S10_excerpts.json、S10_integration.md、decisions/2026-10-10_user_decisions.jsonを同一コミットで読む。進行中2.3候補があれば作業を捨てず差分適用し2.4新候補へ固定。T09→T10→T11と保存済み30案→T06→T12。一括で置換/欠落/局所表示/字体対策/Excel再現/再計算/全ログを実施。C11は保持。
  '20': 2.4新候補を固定し全R01-R14/Q01-Q14を元資料から独立評価。承認欠落/置換を原データ検証済みと誤表示しない。C11未免除。初回全範囲の評価は差分だけで済ませない。
  '30': 指摘前は待機。20の固定候補と問題IDから再現/原因/変更案/影響/再検証を一通にまとめ、reports/30へ返す。10が適用し20が再評価。Excelは編集しない。
  '40': GitHubの同一コミットのPLAN・STATE・10/20/30報告とroles/40.mdを読む。当該フォルダのコミット履歴と必要な過去版・差分を確認し、日時/担当/工程/実施内容/検証結果/成果物と根拠の直近10件表を表示。更新指示で再取得。書込み・完成昇格・別チャット監視は行わない。
  first_user_action: 実行担当00/10/20/30の4チャットと閲覧専用40を同じプロジェクトで開設し、ROLE指定の開始文を送る。mdを保存できない場合はGitHubの現在コミットを取得して同じ版のPLAN/STATE/必要報告を読み該当startupを実行するよう指示する。40はroles/40.mdも読む。モデルは実際の選択欄で設定。GitHubだけでは起動しない。
change_management:
  authorization: 2026-10-09、ユーザーが40の共有指示への組込みと、今後の追加指示の自動組込み・再構成による最適化を依頼。
  trigger: この計画チャットで本プロジェクトの追加指示を受けた際に適用する。無人の定期監視や他チャットからの自動収集を意味しない。
  procedure:
  - 現在HEADと現行PLAN/STATE/必要報告を読み、稼働中の工程と書込み競合を確認
  - 目的・期限・一回性・再現性・算出方法・元資料・受入基準との矛盾と変更の影響を確認
  - 承認済み範囲の変更を最小差分で組み込み、不要な重複や受渡しを減らす
  - 契約を変えない閲覧・案内変更はoperations_revisionを更新。契約に影響する変更はrevisionと再評価・依存を更新し00が状態を統合
  - 構造/既存機械検査/変更対象に必要な確認を行い、未検証の完了や稼働状態を書かない
  - 現在HEADを期待値にした非強制更新で保存し、結果を読戻してコミットと変更点を報告
  scope_boundary: 明示された目的・処理範囲・期限・原本保護・外部共有先と共有内容・重要な制約を独断で変更しない。新たな権限や重要な判断が必要な場合だけ確認する。
  contract_change_20261010:
    revision: '2.3'
    reason: ユーザーがS10全体精読・不足情報の補完・追加工程・GitHub指示書とJSON更新を明示依頼。
    implementation: 計画/S10抽出根拠/STATEの再開情報/版移行検査を更新。10/20/30旧報告と候補JSONはその候補の歴史的証拠として不変。
    state_write_exception: 今回だけ計画担当が明示依頼により計画変更と既存保存報告の状態整合を更新。通常のSTATE.writerは00。
    evaluation: 2.2候補v1のFAILと30提案を保存。新2.3候補は全独立評価。未適用を適用済みとしない。
  operations_history:
  - version: 2.4.4
    date: '2026-10-12'
    change: ROLE00へのユーザー明示判断により、印刷確認コピーの構造受入範囲を注記対象3シートと確定。完成ブックの15シート要件は維持。
    impact: 保存済み実測（3シート/148グラフ部品/15注記/SHA一致/元コピー不変）を構造範囲に限り受入。日本語実描画・全生成再実行・再計算・候補評価・E20-04全体は未完了。次担当10、次単位は再現ZIP内の機械固有パス修正と手順・環境記録の収録。
  - version: 2.4.3
    date: '2026-10-10'
    change: 共有画面を計画チャットと00で分担。別枠の実処理/詳細フロー/3Dファイル概要アトラスと期限までの毎時更新を追加。Siteは未公開。
    impact: 解析契約2.4・候補・STATE・実行報告は変更なし。最終添付は10が固定候補と実manifestへ対応付け。
  - version: 2.2.1
    date: '2026-10-09'
    change: 閲覧専用40と履歴一覧/更新手順、今後の指示組込み手順、GitHub直読みによるmd保存不要の開始方法を追加。
    impact: 計算・入力・要件・候補・評価・受入条件は変更なし。STATE/実行報告/候補は更新しない。解析契約revisionは2.2のまま。
  - version: 2.4.1
    date: '2026-10-10'
    change: 既存全ログ契約の閲覧方式を時系列へ具体化。原文/要約/実報告/保存時刻の分類と未収録を明示。
    impact: 解析入力/算出/評価契約revision2.4不変。10の進行中コード/報告/候補と00のSTATEは変更しない。00が次回STATE更新時に表示運用版のみ反映。
  contract_change_20261010_v24:
    revision: '2.4'
    reason: ユーザーがC04置換/C10欠落/C12放置/C09未算出と品質修正、全ログ別添/簡易文を明示。C11は未指定。
    state_write_exception: 既存自動組込みと今回具体指示の計画反映として再開情報のみ更新。通常writer00を維持。
    applied_to_workbook: false
references:
  model_docs: https://learn.chatgpt.com/docs/models
  model_note: 役割と推論設定は速度・重要性への設計判断。公式の用途説明を確認済み。利用可否は実際の選択欄で確認。
  holiday: https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html
  xls_reader: https://github.com/python-excel/xlrd/blob/master/README.rst
  note: xlrdの通常読取りはVBA・グラフ・数式の実行を提供しない。
  github_actions: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
  workflow_dispatch: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
  design_note: 差分再評価・連携の選択は今回の期限と一回性に対する設計判断。再評価の短縮量は未計測。
reevaluation:
  first_review: 初候補は全要件・全必須指標・出所・計算・表示を20が独立評価。全機械検査を実行する。
  every_candidate:
  - 候補Excelは同じ保存IDの新しい版にし、評価中の固定版を上書きしない
  - 集計検査JSONと10の報告を同時更新
  - 全指標の安価な件数・分母・比率・依存・版検査を毎回実行
  - 変更指標と依存する比較表・説明・グラフの影響閉包を求める
  - 20が影響範囲とC03/C04を元資料から再確認し、新候補へ判定を固定
  - 最終候補の保存/開封/表示/再現を検査し00へ渡す
  candidate_identity:
  - 保存ID
  - 保存版
  - xlsxのSHA256
  - 検査JSONのcandidate_fingerprint
  - 入力ハッシュ
  - 定義ハッシュ
  - テンプレートハッシュ
  - 解析コードの固定コミット
  fingerprint: 検査JSON全体をJSON sort_keys=true, ensure_ascii=false, separators=(comma,colon), allow_nan=falseで正規化しUTF-8のSHA256。fingerprint自身はJSONへ入れず報告へ入れる。
  impact_rule: 変更した指標・元セル・根拠・定義・コードを起点に依存先を再帰追加する。比較文・グラフ・分析要点への対応は20が確認。依存一覧が不完全なら全範囲へ戻す。
  reuse_conditions:
  - 初回の独立評価が確定版にある
  - 入力・定義・テンプレート・コードコミット・計画版・必須指標台帳が同じ
  - 当該指標と根拠ハッシュと依存元が同じ
  - 初回にPASSで、今回の影響閉包の外
  - 今回の全機械検査と最終表示保持検査が合格
  reuse_record: reports/20のreused_fromへ元候補fingerprint・元評価コミット・検査IDと再利用理由を残す。古い候補全体のPASSを新候補へコピーしない。
  invalidate: 入力/定義/テンプレート/コード/計画版/台帳の変更、追跡不能、欠落、前回FAIL/HELDは評価再利用不可。全候補を再検査する。コード変更時の関数依存推定による免除は今回は実装しない。
  provided_aggregate: 個票なしの提供平均/補正/得点はkind=providedとして出所と転記を独立確認。機械が平均を再算出したと称しない。
  outputs: 20は今回のnewly_checked/reused_from/held/issuesと全候補の判定を一通の報告へまとめる。30は一括の修正案と影響一覧を返す。
  efficiency_measure: 初回と再評価ごとに抽出・機械検査・AI評価・受渡しの実測分数、変更/再評価/再利用指標数を10/20報告へ残す。推定の効率率を作らない。
machine_contract:
  schema: care_candidate/v1
  path: care-insurance-analysis/checks/candidate.json
  package_fields:
  - schema
  - plan_revision
  - candidate:{id,version,sha256}
  - input_hashes:{S01:sha256,...}
  - definitions_sha256
  - template_sha256
  - code_commit
  - required_metrics:[id,...]
  - metrics:[metric,...]
  metric_required:
  - id
  - status
  - kind
  - value
  - population
  - unit
  - period
  - source_ref
  - evidence_sha256
  metric_optional:
    count: partsを持つ場合は整数内訳の合計がvalueと完全一致
    ratio/mean: numerator, denominator; 内部値の絶対誤差1e-10、分母>0。比率は0..1、百分率へ変換済みの値を入れない。
    difference_pp: depends_on=[市比率ID,比較先比率ID]、値は100*(市-比較先)
    provided: verification_scopeで提供値転記の範囲を表示。個票なし再算出不可。
    held/missing/not_applicable: reason必須。missingとnot_applicableのvalueはnull。heldの比較先はvalidとして使えない。
    depends_on: 数値の依存ID。説明・グラフへの対応は別途評価。
  inventory: required_metricsはT02の全必須指標IDから作る。20が要件対応と台帳の網羅性を独立確認。JSON検査だけでは指標漏れの不存在を保証しない。
  evidence_hash: 入力ハッシュ・シート/セル・期間・母集団・補正・元値を正規化してSHA256。20が実際の元資料と確認。
  commands:
  - python3 -m unittest discover -s care-insurance-analysis/tools -p "test_*.py" -v
  - python3 care-insurance-analysis/tools/verify_handoff.py
  workbook_hash: 10/20の実行環境で実ExcelのSHA256をcandidate.sha256と照合。Actionsは参照メタデータしか持たず実Excel保持/表示を保証しない。
  startup_result: 候補未生成時はmetadata only/NOT_STARTED_OR_NO_CANDIDATE。初期検査PASSを本解析合格へ読み替えない。
  revision_transition: STATE.plan_changeの前版を旧報告/旧候補として保存し、旧計画の評価を新計画へ付替えない。新版候補がまだない場合はREVISED_PLAN_AWAITING_NEW_CANDIDATE、新版評価待ちはevaluation_pending_plan_revision。メタデータ受渡し成功は解析合格ではない。
  supplement_contract: S10-*独立出所を維持。C04置換表示だけprovided_substituteとしてユーザー承認に対応付け。C10欠落/C12除外/C09未算出は採用null/比較なし。既存care_candidate/v1の機械状態は互換held/not_applicable等を維持し、新presentation_status/decision_refへ表示区分を別記。未算出や提供値をvalid再算出にしない。
    旧S01調査行はheldのまま保持し、新S10置換行は転記確認後にstatus=valid, kind=provided, verification_scope=年度独自提供値の転記確認、presentation_status=provided_substituteとする。統計の再計算合格ではない。比較依存に使用不可。
  release_authority: 機械は完成昇格もSTATE更新も実施しない。20の独立判定を00が統合し、10がrelease_gatesに従って提出。
```

運用2.4.1：過去会話・実報告をタイムライン表示。解析契約2.4と候補評価は変更しない。過去全文取得は未完了。
