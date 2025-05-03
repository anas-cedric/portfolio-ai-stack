"""
Preset Financial Data Module.

This module provides pre-processed financial data for use in the RAG system,
eliminating the need for real-time document processing while maintaining
the same data structure and interface.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PresetFinancialData:
    """
    Provider of preset financial data for the RAG system.
    
    This class simulates the output of a document processing pipeline
    without requiring actual processing, using pre-generated data.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the preset financial data provider.
        
        Args:
            data_path: Optional path to preset data files. If None, uses built-in data.
        """
        self.data_path = data_path
        self.preset_data = self._load_preset_data()
        logger.info(f"Loaded {len(self.preset_data)} preset financial documents")
    
    def _load_preset_data(self) -> List[Dict[str, Any]]:
        """
        Load preset financial data from files or use built-in data.
        
        Returns:
            List of financial document dictionaries
        """
        if self.data_path and os.path.exists(self.data_path):
            try:
                with open(os.path.join(self.data_path, "preset_financial_data.json"), "r") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Could not load preset data from {self.data_path}: {str(e)}")
                logger.info("Using built-in preset data instead")
                
        # If no external data or loading failed, use built-in preset data
        return self._get_builtin_preset_data()
    
    def _get_builtin_preset_data(self) -> List[Dict[str, Any]]:
        """
        Get built-in preset financial data.
        
        Returns:
            List of financial document dictionaries
        """
        # Generate a collection of preset financial documents covering various topics
        return [
            # S&P 500 information
            {
                "id": "fund_sp500_overview",
                "content": "The S&P 500 (Standard & Poor's 500) is a stock market index that tracks the performance of 500 large companies listed on stock exchanges in the United States. It is one of the most commonly followed equity indices and is considered to be a representation of the U.S. stock market and the U.S. economy. The S&P 500 is a capitalization-weighted index, meaning companies with larger market capitalizations have a greater impact on the index's performance.\n\nThe index covers approximately 80% of available market capitalization. Companies in the S&P 500 are selected by a committee based on factors including market capitalization (minimum $8.2 billion), liquidity, domicile, public float, sector classification, financial viability, length of time publicly traded, and stock exchange listing. The S&P 500 is maintained by S&P Dow Jones Indices.",
                "metadata": {
                    "title": "S&P 500 Index Overview",
                    "source": "financial_knowledge_base",
                    "category": "fund_knowledge", 
                    "fund_type": "index", 
                    "tags": ["index", "stock market", "equity", "large-cap"]
                }
            },
            # Vanguard S&P 500 ETF (VOO)
            {
                "id": "fund_voo_example",
                "content": "The Vanguard S&P 500 ETF (VOO) is an exchange-traded fund that tracks the performance of the S&P 500 Index. With an expense ratio of just 0.03%, it is one of the lowest-cost ETFs available for investing in the S&P 500. The fund provides investors with exposure to 500 of the largest U.S. companies, which span approximately 80% of the U.S. equity market capitalization.\n\nVOO is managed by Vanguard, one of the largest investment management companies globally known for its low-cost investment products. The ETF was launched on September 7, 2010, and has since grown to be one of the largest ETFs in the market with over $800 billion in assets under management. The fund distributes quarterly dividends and has a 30-day SEC yield of approximately 1.3% (as of recent data).\n\nAs a passively managed index fund, VOO aims to replicate the performance of the S&P 500 by holding all the stocks in the index in approximately the same proportions as their weightings in the index. This approach typically results in lower turnover and greater tax efficiency compared to actively managed funds.",
                "metadata": {
                    "title": "Vanguard S&P 500 ETF (VOO)",
                    "source": "Vanguard, VOO",
                    "category": "fund_knowledge", 
                    "fund_provider": "Vanguard", 
                    "fund_ticker": "VOO", 
                    "fund_type": "ETF", 
                    "tags": ["ETF", "S&P 500", "index fund", "low cost", "large-cap", "Vanguard"]
                }
            },
            # Vanguard Total Stock Market ETF (VTI)
            {
                "id": "fund_2863ec0adf",
                "content": "The Vanguard Total Stock Market ETF (VTI) is an exchange-traded fund designed to track the performance of the CRSP US Total Market Index, which represents approximately 100% of the investable U.S. stock market and includes large-, mid-, small-, and micro-cap stocks regularly traded on the New York Stock Exchange and Nasdaq.\n\nVTI offers investors a way to gain diversified exposure to the entire U.S. equity market through a single investment vehicle. The fund has an expense ratio of 0.03%, making it one of the lowest-cost options for broad market exposure. Since its inception in 2001, VTI has grown to manage over $1.2 trillion in assets (as of recent data).\n\nThe ETF holds more than 4,000 stocks across various sectors, with current sector allocations approximately: Technology (29.8%), Consumer Discretionary (14.2%), Health Care (12.9%), Financials (12.7%), Industrials (9.7%), Communication Services (8.1%), Consumer Staples (5.2%), Energy (2.6%), Real Estate (2.4%), Utilities (1.7%), and Materials (0.7%). The fund's 10 largest holdings typically account for about 20-25% of its total assets.\n\nVTI is appropriate for investors seeking long-term growth and broad diversification across the entire U.S. stock market. It can serve as a core holding in a portfolio and is often used in various asset allocation strategies.",
                "metadata": {
                    "title": "Vanguard Total Stock Market ETF (VTI)",
                    "source": "Vanguard, VTI",
                    "category": "fund_knowledge", 
                    "id": "fund_2863ec0adf", 
                    "fund_provider": "Vanguard", 
                    "fund_ticker": "VTI", 
                    "fund_type": "ETF", 
                    "tags": ["ETF", "total market", "broad market", "index fund", "diversification", "Vanguard"]
                }
            },
            # Apple Inc. (AAPL) - Profile
            {
                "id": "fund_aapl_profile",
                "content": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allows customers to discover and download applications and digital content, such as books, music, video, games, and podcasts.\n\nApple's key investment highlights include: 1) A strong ecosystem that creates high switching costs for users, 2) Consistent innovation in hardware and services, 3) Premium pricing power and high margins, 4) Significant recurring revenue from services, 5) Strong balance sheet with substantial cash reserves, and 6) Commitment to shareholder returns through dividends and share repurchases.\n\nPotential investment risks include: 1) Heavy reliance on iPhone sales which account for approximately 50% of revenue, 2) Increasing competition in all product categories, 3) Regulatory scrutiny around App Store practices, 4) Dependency on China for both manufacturing and as a significant market, and 5) Product cycles that can lead to sales volatility.",
                "metadata": {
                    "title": "Apple Inc. (AAPL): Company Profile and Investment Analysis",
                    "source": "AAPL",
                    "category": "fund_knowledge",
                    "company_name": "Apple Inc.",
                    "fund_ticker": "AAPL",
                    "fund_type": "stock",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "description": "Technology company that designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                    "investment_highlights": ["Strong ecosystem", "Premium pricing power", "Services growth", "Cash reserves", "Shareholder returns"],
                    "investment_risks": ["iPhone dependency", "Competition", "Regulatory risks", "China dependency", "Product cycles"],
                    "tags": ["technology", "consumer electronics", "iPhone", "services", "hardware"]
                }
            },
            # Apple Inc. (AAPL) - Stock Analysis
            {
                "id": "fund_aapl_123456",
                "content": "Apple Inc. is a technology company that designs, manufactures, and markets smartphones (iPhone), personal computers (Mac), tablets (iPad), wearables and accessories (including Apple Watch, AirPods), and sells various related services. The company has a market capitalization of over $2.7 trillion, making it one of the largest companies globally by market value.\n\nFinancial Performance: Apple generated approximately $380 billion in revenue in the latest fiscal year, with iPhone representing about 52% of total revenue, followed by Services at 22%, Mac at 11%, Wearables, Home, and Accessories at 9%, and iPad at 6%. The company maintains strong gross margins of around 43% and an operating margin of approximately 30%. Apple's Services segment, which includes the App Store, Apple Music, Apple TV+, iCloud, and Apple Pay, continues to grow at double-digit rates and carries higher margins than hardware products.\n\nInvestment Thesis: The investment thesis for Apple centers around several key factors: 1) The company's ecosystem creates high switching costs for users, leading to customer loyalty and recurring revenue; 2) The Services segment is growing rapidly and provides a more stable revenue stream than hardware sales; 3) Apple's focus on premium positioning allows it to maintain high margins; 4) Strong balance sheet with approximately $160 billion in cash and marketable securities; 5) Consistent innovation in both hardware and software; and 6) Significant shareholder returns through dividends and share repurchases.\n\nRisks: Key risks include: 1) Competition in all product categories; 2) Regulatory scrutiny of the App Store business model; 3) Challenges in establishing new product categories to reduce reliance on the iPhone; 4) Global supply chain disruptions; and 5) Foreign exchange impacts on international sales.",
                "metadata": {
                    "title": "Apple Inc. (AAPL) Stock Analysis",
                    "source": "AAPL",
                    "category": "fund_knowledge",
                    "id": "fund_aapl_123456",
                    "company_name": "Apple Inc.",
                    "fund_ticker": "AAPL",
                    "fund_type": "stock",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "description": "Technology company that designs, manufactures, and markets consumer electronics.",
                    "investment_thesis": "Strong ecosystem creating high switching costs and customer loyalty, growing services segment, premium positioning, strong balance sheet, consistent innovation, and significant shareholder returns.",
                    "tags": ["technology", "iPhone", "services", "consumer electronics"]
                }
            },
            # Investment Principles - Portfolio Rebalancing
            {
                "id": "prin_ce8cf8ccb6",
                "content": "Portfolio rebalancing is a strategic process of realigning the weightings of assets in an investment portfolio to maintain the original or desired level of asset allocation. As market movements cause the value of assets to fluctuate, the original allocation percentages shift. Rebalancing involves buying or selling assets to return to the target allocation.\n\nThe primary purpose of rebalancing is risk management rather than maximizing returns. Without rebalancing, a portfolio can drift toward an allocation that takes on too much risk or not enough risk to meet the investor's goals. For example, during a bull market, the equity portion of a portfolio may grow significantly, increasing the portfolio's overall risk beyond the investor's tolerance level.\n\nThere are several approaches to rebalancing: 1) Calendar rebalancing - adjusting at predetermined time intervals (quarterly, semi-annually, or annually); 2) Percentage-of-portfolio rebalancing - adjusting when an asset class deviates from the target allocation by a predetermined percentage (e.g., 5%); and 3) Tactical rebalancing - adjusting based on economic outlooks or market conditions.\n\nConsiderations when rebalancing include transaction costs, tax implications, and market conditions. In taxable accounts, rebalancing can trigger capital gains taxes, so it's important to consider tax-efficient rebalancing strategies, such as directing new investments to underweighted asset classes, using tax-advantaged accounts for rebalancing, or timing rebalancing to coincide with tax-loss harvesting opportunities.\n\nThe optimal frequency of rebalancing depends on factors such as market volatility, transaction costs, and the investor's risk tolerance. Research suggests that annual or semi-annual rebalancing often provides a reasonable balance between maintaining target allocations and minimizing costs.",
                "metadata": {
                    "title": "Portfolio Rebalancing: Principles and Strategies",
                    "source": "Investment Principles Database",
                    "category": "investment_principles",
                    "id": "prin_ce8cf8ccb6",
                    "principle_type": "portfolio_management",
                    "risk_level": "moderate",
                    "time_horizon": "medium_to_long_term",
                    "tags": ["rebalancing", "asset allocation", "portfolio management", "risk management", "investment strategy"]
                }
            },
            # Inflation Hedge Investments
            {
                "id": "prin_inflation_hedge",
                "content": "Inflation hedging is an investment strategy aimed at protecting a portfolio from the decreased purchasing power of currency that results from the loss of value due to rising prices. Several asset classes have historically served as effective inflation hedges.\n\nTreasury Inflation-Protected Securities (TIPS) are government bonds explicitly designed to protect against inflation. The principal value of TIPS adjusts based on changes in the Consumer Price Index (CPI), with interest payments calculated on the adjusted principal. This direct link to inflation makes TIPS one of the most straightforward inflation hedges available to investors.\n\nCommodities often perform well during inflationary periods because their prices typically rise as inflation increases. Gold has traditionally been viewed as an inflation hedge and a store of value during economic uncertainty. Energy commodities like oil and natural gas, along with industrial metals and agricultural products, can also provide inflation protection since their prices tend to rise with inflation.\n\nReal estate investments, both through direct ownership and Real Estate Investment Trusts (REITs), can offer inflation protection as property values and rental income often increase during inflationary periods. Real estate can serve as a particularly effective hedge when inflation is driven by strong economic growth.\n\nEquities, particularly stocks of companies with pricing power, can provide inflation protection in the medium to long term. Companies in sectors such as consumer staples, healthcare, energy, and certain industrials may be better positioned to pass higher costs on to consumers, maintaining profit margins during moderate inflation. Value stocks have historically outperformed growth stocks during periods of higher inflation.\n\nCommodity-linked stocks, such as those in the energy, mining, and agricultural sectors, can benefit from rising commodity prices during inflationary periods. These companies can often increase their earnings and dividends faster than the inflation rate when commodity prices rise.\n\nInflation-linked bonds issued by governments outside the U.S. can provide diversification benefits to a portfolio seeking inflation protection, as inflation rates can vary significantly across countries and regions.",
                "metadata": {
                    "title": "Inflation-Hedging Investment Strategies",
                    "source": "Investment Principles Database",
                    "category": "investment_principles",
                    "id": "prin_inflation_hedge",
                    "principle_type": "inflation_protection",
                    "risk_level": "moderate",
                    "time_horizon": "medium_to_long_term",
                    "tags": ["inflation", "hedge", "TIPS", "commodities", "real estate", "energy stocks", "value stocks"]
                }
            },
            # Market Volatility Strategies
            {
                "id": "prin_volatility_strategies",
                "content": "Market volatility refers to the rate at which the price of securities increases or decreases. High volatility is associated with large swings in either direction, while low volatility indicates more stable price movements. Volatility is often measured using the VIX index for the S&P 500 or standard deviation of returns for individual securities.\n\nInvestors can employ several strategies to navigate market volatility effectively. Diversification across asset classes, sectors, and geographies remains one of the most effective approaches to managing volatility. Different assets often respond differently to economic conditions and market events, potentially smoothing overall portfolio volatility.\n\nDollar-cost averaging involves investing a fixed amount at regular intervals regardless of market conditions. This approach can reduce the impact of volatility by purchasing more shares when prices are lower and fewer when prices are higher, potentially lowering the average cost per share over time.\n\nDefensive sectors such as utilities, consumer staples, and healthcare traditionally exhibit lower volatility than cyclical sectors like technology or consumer discretionary. During periods of high market volatility, increasing allocation to these defensive sectors may help stabilize portfolio returns.\n\nImplementing an options strategy, such as covered calls or protective puts, can help manage volatility. Covered calls can generate income in flat or slightly declining markets, while protective puts can limit downside risk during market corrections.\n\nLow-volatility ETFs specifically target stocks with historically lower price fluctuations. These funds aim to provide equity market exposure with reduced volatility compared to the broader market.\n\nMaintaining a sufficient cash reserve during volatile periods provides both protection against forced selling of depressed assets and the ability to capitalize on opportunities that arise when quality investments become undervalued.\n\nIt's important to remember that volatility itself isn't necessarily negative—it creates opportunities for disciplined investors. Additionally, the appropriate response to volatility depends on an investor's time horizon, with longer-term investors typically better positioned to weather short-term fluctuations.",
                "metadata": {
                    "title": "Strategies for Managing Market Volatility",
                    "source": "Investment Principles Database",
                    "category": "investment_principles",
                    "id": "prin_volatility_strategies",
                    "principle_type": "risk_management",
                    "risk_level": "moderate_to_high",
                    "time_horizon": "short_to_long_term",
                    "tags": ["volatility", "risk management", "diversification", "defensive sectors", "options strategies", "dollar-cost averaging"]
                }
            },
            # Bond Duration and Interest Rates
            {
                "id": "prin_bond_duration",
                "content": "Bond duration is a measure of a bond's sensitivity to interest rate changes, expressed in years. It represents the weighted average time until all of a bond's cash flows (interest payments and principal repayment) are received. Higher duration bonds experience greater price changes when interest rates move compared to lower duration bonds.\n\nThe relationship between bond prices and interest rates is inverse: when interest rates rise, bond prices fall, and when interest rates fall, bond prices rise. Duration quantifies this relationship. For example, a bond with a 5-year duration will decrease in value by approximately 5% if interest rates rise by 1 percentage point, or increase in value by approximately 5% if interest rates fall by 1 percentage point.\n\nFactors that affect a bond's duration include: 1) Maturity - longer maturity bonds generally have higher durations; 2) Coupon rate - higher coupon bonds have lower durations than similar bonds with lower coupons; and 3) Yield - as a bond's yield increases, its duration typically decreases.\n\nIn rising interest rate environments, investors often shift toward shorter-duration bonds to reduce price sensitivity. Conversely, in falling rate environments, longer-duration bonds may be preferred to maximize price appreciation. Bond laddering (buying bonds with staggered maturities) can help manage duration risk by diversifying exposure across different points on the yield curve.\n\nIn addition to duration, investors should consider convexity, which measures how duration itself changes as yields change. Positive convexity (found in most conventional bonds) means the rate of price increase when yields fall exceeds the rate of price decrease when yields rise by the same amount. This characteristic is generally beneficial for bondholders.\n\nUnderstanding duration is critical for fixed-income investors, particularly when constructing portfolios to match specific liability timelines or when attempting to position a portfolio for anticipated interest rate movements.",
                "metadata": {
                    "title": "Bond Duration and Interest Rate Risk Management",
                    "source": "Investment Principles Database",
                    "category": "investment_principles",
                    "id": "prin_bond_duration",
                    "principle_type": "fixed_income",
                    "risk_level": "low_to_moderate",
                    "time_horizon": "short_to_long_term",
                    "tags": ["bonds", "duration", "interest rates", "fixed income", "yield curve", "convexity"]
                }
            },
            # Retirement Planning - Withdrawal Strategies
            {
                "id": "prin_retirement_withdrawal",
                "content": """Retirement withdrawal strategies focus on how to systematically withdraw from retirement accounts to maximize longevity of funds while maintaining desired lifestyle. The optimal approach depends on individual circumstances, including portfolio size, life expectancy, other income sources, and risk tolerance.

The 4% Rule suggests withdrawing 4% of the portfolio in the first year of retirement, then adjusting that amount annually for inflation. This rule aims to provide a high probability that the portfolio will last at least 30 years, based on historical market returns. Critics note that the rule may be too conservative in some market environments and too aggressive in others.

Dynamic withdrawal strategies adjust the withdrawal rate based on market performance. In strong market years, withdrawals might increase slightly, while in down years, withdrawals may be reduced or remain flat. Examples include the Guyton-Klinger rule and the Yale Endowment Model adjusted for individual investors.

Bucket strategies segment retirement assets into different time horizon "buckets" - typically short-term (1-5 years), medium-term (5-15 years), and long-term (15+ years). The short-term bucket holds cash and high-quality short-term bonds to fund immediate needs, allowing longer-term buckets to remain invested for growth.

The Required Minimum Distribution (RMD) method uses the IRS RMD calculation methodology to determine annual withdrawals, dividing the account balance by the life expectancy factor. This approach automatically adjusts withdrawals based on portfolio performance and increases the withdrawal percentage as the retiree ages.

For many retirees, a combination of approaches works best. For example, ensuring 5-10 years of essential expenses are covered by guaranteed income sources (Social Security, pensions) and short-term fixed income investments, while maintaining growth investments for later retirement years.

Tax efficiency in withdrawals can significantly extend portfolio longevity. Generally, it's advantageous to withdraw from taxable accounts first, then tax-deferred accounts (traditional IRAs, 401(k)s), and finally tax-free accounts (Roth IRAs). However, opportunities for tax bracket management may suggest modifications to this approach.""",
                "metadata": {
                    "title": "Retirement Withdrawal Strategies",
                    "source": "Investment Principles Database",
                    "category": "investment_principles",
                    "id": "prin_retirement_withdrawal",
                    "principle_type": "retirement_planning",
                    "risk_level": "moderate",
                    "time_horizon": "long_term",
                    "tags": ["retirement", "withdrawal strategy", "4% rule", "RMD", "bucket strategy", "sequence risk", "longevity risk"]
                }
            },
            # Test embedding for voyage model
            {
                "id": "test_voyage_embedding",
                "content": "This is a test document to verify that the voyage embedding model is working correctly. It contains financial terms like stocks, bonds, portfolio diversification, asset allocation, market volatility, bull market, bear market, dividend yield, and price-to-earnings ratio. The document is used to test the semantic search functionality of the RAG system.",
                "metadata": {
                    "title": "Test Document for Voyage Embeddings",
                    "source": "Test Document",
                    "category": "investment_principles"
                }
            }
        ]
    
    def get_documents(self, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get preset financial documents, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
            limit: Maximum number of documents to return
            
        Returns:
            List of financial document dictionaries
        """
        if category:
            filtered_docs = [doc for doc in self.preset_data if doc.get("metadata", {}).get("category") == category]
            return filtered_docs[:limit]
        
        return self.preset_data[:limit]
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific financial document by ID.
        
        Args:
            doc_id: The document ID to search for
            
        Returns:
            The document dictionary or None if not found
        """
        for doc in self.preset_data:
            if doc.get("id") == doc_id:
                return doc
        return None
    
    def get_mock_embedding(self, text: str, dim: int = 1024) -> List[float]:
        """
        Generate a deterministic mock embedding for a text.
        
        This isn't a real embedding, but creates deterministic vectors
        that maintain the same vector for the same text input, allowing
        for consistent testing without real embedding models.
        
        Args:
            text: The text to generate a mock embedding for
            dim: The embedding dimension
            
        Returns:
            A deterministic mock embedding vector
        """
        # Use the hash of the text as a seed for reproducibility
        np.random.seed(hash(text) % (2**32))
        
        # Generate a deterministic random vector
        vector = np.random.normal(0, 1, dim).astype(np.float32)
        
        # Normalize to unit length
        vector = vector / np.linalg.norm(vector)
        
        return vector.tolist()

    def save_preset_data(self, file_path: str) -> bool:
        """
        Save the preset data to a file.
        
        Args:
            file_path: Path to save the preset data to
            
        Returns:
            Boolean indicating success
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(self.preset_data, f, indent=2)
            logger.info(f"Saved preset data to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save preset data to {file_path}: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize preset data
    preset_data = PresetFinancialData()
    
    # Print available documents
    print(f"Loaded {len(preset_data.preset_data)} preset financial documents")
    
    # Get documents by category
    fund_docs = preset_data.get_documents(category="fund_knowledge", limit=5)
    print(f"Found {len(fund_docs)} fund knowledge documents")
    
    # Generate a mock embedding
    sample_text = "What is the S&P 500 index?"
    embedding = preset_data.get_mock_embedding(sample_text)
    print(f"Generated mock embedding of dimension {len(embedding)}")
    
    # Save to file for future use
    preset_data.save_preset_data("data/preset_financial_data.json") 