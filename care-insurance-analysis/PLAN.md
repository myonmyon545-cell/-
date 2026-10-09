# 介護保険データ解析 AI実行仕様

解析契約2.2 / 運用版2.2.1 / 2026-10-09 / 主対象：処理対象データ群.xlsx / 計画・進捗の正本はGitHub

この仕様はAI用のYAML設定・工程契約であり、単独で実行するプログラムではない。`ROLE=00|10|20|30|40` を指定する。未指定は00。最初にmeta・invariants・sources・自ROLE・github_handoff・startupを読み、その工程に必要な算出規則と検査を参照する。最新のユーザー指示、現行共通指示、詳細運用を併用する。候補到着前の評価と修正チャットは準備または待機とし、合格報告を作らない。

```yaml
meta:
  schema: care_analysis_execution_v2
  revision: '2.2'
  operations_revision: '2.2.1'
  operations_updated_at: '2026-10-09'
  version_policy: revisionは解析・評価契約、operations_revisionはその契約を変えない閲覧・案内の運用版。運用だけの変更は候補の評価を無効化しない。入力・定義・コード・テンプレート・要件・検査・受入条件への変更はrevisionを更新し、既存の再評価規則を適用する。
  project: 介護保険データ解析
  state: planning_complete_analysis_not_started
  canonical_plan: GitHub mainのcare-insurance-analysis/PLAN.md。本ファイルは同じ版の導入用写し。GitHubを読めない場合は確定コミットの写しを使う。
  checked_at: '2026-10-08'
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
  not_executed:
  - 本解析
  - Excel生成と保持試験
  - 実際の4チャット開設
  - 別チャットからの読取り試験
invariants:
- S01だけを主対象とする。複製を合算せず、原本は変更しない。
- R5は形式参照。年度・期間・数値は本文で判定し、過去値を転用しない。
- 数値はコードと表計算で処理し、AIの暗算や生成文を数値の正本にしない。
- 事実、解釈、仮説、実施結果を区別する。未確認は補完しない。
- 最終Excelの書込みは10だけ、STATEの書込みは00だけ。
- 別チャットの自動操作、共有記憶、自動監視を前提にしない。
- 期限が迫っても検査を省略せず、保留・暫定と完成を区別する。
- 今回用のコードでよい。常設サイト、DB、定期実行、汎用ライブラリ、新規GitHub構築を必須にしない。
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
outputs:
  workbook:
    name: R7_介護保険データ解析結果.xlsx
    base: S01_copy
    reference: S03_structure
    preserve: 元14シートの名称、掲載項目、表、目次、印刷構成、148グラフの系列と参照と配置
    add: 先頭の分析要点1シート
    summary: 上部に重点結果、下部に比較表・算出根拠・未解決事項
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
    correction_policy: 根拠が一意の箇所だけ修正し、前後・理由・評価を記録する。
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
    status: held
    resolve: 元送信・集計結果または個票日付で確認。0日だけでは誤りと断定しない。
    withheld: 調査期間の比較と原因説明
    forbidden: R5の7.1日や県平均で置換
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
  board_limit: 1ファイル20合議体、21以上は複数出力。全出力が揃うまで完了にしない。
  execution_policy: 古いExcel設定を現環境で実施済みとしない。xls読取りや変換はVBA実行とは異なる。
  alternative: 正式定義と代表CSVによる既存出力との一致を検証した場合だけ代替実装。合議体を推測しない。
  deadline_gate: 10月9日にCSVと環境を判断。未提供なら条件待ちを確定し、本体を進める。
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
    work: 候補Excelを作成し保存
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
  T08:
    owner: '10'
    deps:
    - T07
    work: 判定に応じて完成または暫定を保存提出
    output: Excelと再現ZIPと00への報告
    checks:
    - Q12
  split: Ⅰ、Ⅱ、Ⅲ・Ⅳの3処理単位。共通抽出器を使い、章別チャットを増やさない。
  order_optimization: 説明重点のⅠ・Ⅲ・Ⅳを先に、Ⅱは一括抽出。全章の必須範囲を落とさない。
  concurrency: T02とT03は独立範囲なら並行可。同一出力への書込みは直列。
  live_estimate: 未処理単位数×実測単位時間＋生成評価保存受渡し時間の幅。確認待ちは別扱い。
  critical_path_parallel: t01+max(t02+t04+t05,t03)+t06+t07+t08
  critical_path_policy: 実際に並行できない部分は加算し、修正・確認待ちも加える。残り暦時間を全て稼働時間にしない。
milestones:
  dates:
  - target: '2026-10-09T18:00:00+09:00'
    done:
    - T01
    - T02
    - T03
    gate: 出力保持経路、C03照合、C04照会経路、CSV可否
  - target: '2026-10-10T20:00:00+09:00'
    done:
    - T04
    - T05
    - T06
    gate: 全章抽出比較と候補v1
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
release_gates:
  final: 必須掲載・計算・表示・再現・保存が合格し、重要未解決なし。完成と表示。
  provisional: 読めること・原本保持・候補の整合性と既知状態表示は検査済みだが重要未確認が残る。暫定と表示し保留値の結論を抑止。
  failed_integrity: 開けない、参照破損、意図しない変更等なら最終反映を止め、診断と保存済みの確認可能部分を報告。
  deadline_policy: 期限時の暫定提出は品質面の完了を意味しない。C04未解決を完成へ変えない。
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
    future_analysis_code: care-insurance-analysis/src/
    verifier: care-insurance-analysis/tools/verify_handoff.py
    candidate_checks: care-insurance-analysis/checks/candidate.json
    workflow: .github/workflows/care-handoff-check.yml
  startup_read: branchの現在コミットを取得し、PLAN・STATE・必要な報告を同じコミットで直接読む。検索インデックスを待たない。参照コミットを報告に記録。
  write_policy: 00はPLAN/STATE、10はsrc・candidate検査JSON・reports/10、20/30は自分の報告を更新。40は読取り専用。ユーザーから本件の追加指示を受けた計画担当は承認された範囲でPLAN/README/役割の運用定義を更新できるが、STATEと実行報告は各担当の専有を維持する。更新前に現在HEADとファイルSHAを読み、比較交換で競合を検出。強制上書きしない。解析契約revisionを変えるPLAN更新は00が関連STATE/報告の版と再評価状態を整合させ、一つのコミットで反映する。operations_revisionだけの変更ではSTATE/実行報告/候補の版を付け替えない。
  candidate_atomic_update: checks/candidate.jsonとreports/10.jsonは一つのコミットで更新。20は候補ID版SHAとcandidate_fingerprintを報告へ固定。STATE更新は00が後で統合してよい。
  capability_gate: 各役割チャットの初回に直接読取りを試す。接続できなければ確定版の添付へ切替し、00がGitHub正本へ反映。
  runner_limit: ActionsはJSON/コードの検査を実行する。別チャットを起動・遠隔操作・常時監視しない。候補Excel・元資料をActionsから取得する機能は作らない。
  activation_verification: 登録コミットのPLAN・STATE・検査ファイルを読戻し、内容のSHAを比較してから共有開始を報告。Actions実行の成否は実行結果を別途確認。
  fallback: Actionsが起動しない/枠不足/権限不足なら10が同じPython検査を実行し、版付きの結果を報告。機械検査を省略しない。
startup:
  '00': GitHubの同一コミットのPLAN/STATE/報告を読み、TとM、C01-C08、期限、次の操作を表示。今回の登録と検査の実態を確認。本解析完了と表示しない。STATEを単独更新。
  '10': GitHubと入力へのアクセスを確認。T01→T02/T03を開始し、出力保持方式を最優先で試す。src/reports/10へ保存。候補後はmachine_contractを作り全機械検査。Excelと再現ZIPは現在の保存先へ。
  '20': PLAN/STATEと10の報告を確認。候補前は定義・既知問題と検査観点を準備。候補後は初回の全独立評価、修正後はreevaluation。reports/20に対象fingerprintと判定を記録。
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
  operations_history:
  - version: '2.2.1'
    date: '2026-10-09'
    change: 閲覧専用40と履歴一覧/更新手順、今後の指示組込み手順、GitHub直読みによるmd保存不要の開始方法を追加。
    impact: 計算・入力・要件・候補・評価・受入条件は変更なし。STATE/実行報告/候補は更新しない。解析契約revisionは2.2のまま。

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
  release_authority: 機械は完成昇格もSTATE更新も実施しない。20の独立判定を00が統合し、10がrelease_gatesに従って提出。
```

開始文：`ROLE=00`（進捗）、`ROLE=10`（作業）、`ROLE=20`（評価）、`ROLE=30`（修正）、`ROLE=40`（履歴閲覧）のいずれかに「添付のAI実行仕様を読み、該当startupを実行してください。」を添える。モデルはrolesの推奨を実際の選択欄で設定する。

版2.2の変更：承認済み非公開GitHubを共有正本へ移行し、軽量機械検査と版付きの差分再評価を追加。初回は全独立評価、修正後も全数機械検査を行い、AI再評価は影響範囲へ集中する。Drive/Airtableは必要が生じた場合の予備。期限・一回性・再現性・R5形式・manualの条件付き工程を維持。本解析と候補Excelの生成は未実施。

運用版2.2.1の変更：40の読取り専用履歴ビューと追加指示の組込み・検証・保存方針を追加。解析契約2.2および実行記録は維持。履歴ビューは保存済み記録を表示し、保存前の他チャットの稼働状態は取得しない。
