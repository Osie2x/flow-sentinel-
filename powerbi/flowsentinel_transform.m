let
    BasePath = "C:\\FlowSentinel\\data\\processed\\",
    DailyHealth = Csv.Document(
        File.Contents(BasePath & "daily_health_summary.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    PromotedDailyHealth = Table.PromoteHeaders(DailyHealth, [PromoteAllScalars = true]),
    TypedDailyHealth = Table.TransformColumnTypes(
        PromotedDailyHealth,
        {
            {"run_date", type date},
            {"total_records", Int64.Type},
            {"completeness", type number},
            {"error_rate", type number},
            {"throughput", type number},
            {"anomaly_rate", type number},
            {"composite_score", type number}
        }
    )
in
    TypedDailyHealth

