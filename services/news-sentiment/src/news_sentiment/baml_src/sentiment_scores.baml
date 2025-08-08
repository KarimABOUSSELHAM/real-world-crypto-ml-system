class SentimentScore {
  coin string
  score "1" | "-1"
}
// Defining a data model.
class SentimentScores {
  scores SentimentScore[]
  reason string @description(#"
    The reason for the sentiment scoring
  "#)
}

// Create a function to extract the resume from a string.
function ExtractSentimentScores(news: string) -> SentimentScores {
  // Specify a client as provider/model-name
  // you can use custom LLM params with a custom client name from clients.baml like "client CustomHaiku"
  client "CustomSonnet4" // Set OPENAI_API_KEY to use this client.
  prompt #"
    You are an expert crypto financial analyst with deep knowledge of market dynamics 
    and sentiment analysis.
    Analyze the following news story and determine its potential impact on crypto asset prices.
    Focus on both direct mentions and indirect implications for each asset.

    Do not output data for a given coin if the news is not relevant to it.

    Extract from this content:
    {{ news }}

    {{ ctx.output_format }}
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test goldman_sachs_news {
  functions [ExtractSentimentScores]
  args {
    news #"
      Goldman Sachs says it is going to buy soon 1 M BTC and sell 1 M ETH.
    "#
  }
}
