from .models import IexApiKey, KeyStats, BalanceSheet, CashFlow, IncomeStatement
import os
import datetime
from ..stocks.models import Stock
from ..mail_relay.tasks import send_mail
import iexfinance.account  # somehow these have to be imported like this and can not be imported globally?? 
import iexfinance.stocks

# Either obtain the sandbox api key or not 
class IexFinanceApi():
    def __init__(self, tickers):
        # By default set everything to the sandbox environment so that no messages are used by accident
        self.set_sandbox()
        self.verifiy_account_information()
        self.tickers = tickers

    # Obtain the metadata and store it in the class so that we are able to see how many messages we have left
    # In case certain thresholds are reached we send email alerts
    def verifiy_account_information(self):
        meta_data = iexfinance.account.get_metadata(token=self.IexApiObject.token)
        messages_used = meta_data.loc['messagesUsed'][0]
        messages_limit = meta_data.loc['messageLimit'][0]
        messages_available = messages_limit - messages_used

        # See whether we have exceeded on of the notification thresholds
        old_threshold = (messages_limit - self.IexApiObject.messages_available)/messages_limit*100 if messages_limit else 0
        new_threshold = (messages_limit - messages_available)/messages_limit*100 if messages_limit else 0
        notification_thresholds = [25, 50, 75, 80, 85, 90, 95]

        for threshold in notification_thresholds:
            # In case we have exceeded the threshold send the mail and update the threshold variable
            if ((old_threshold < threshold) and (new_threshold >= threshold)):
                targets = ['thresholding@dejong.lu']
                sender = "finance@dejong.lu"
                subject = 'API %f\% threshold exceeded' % (threshold)
                message = 'Hello,\nThe API has exceeded the %f\%t threshold in the sandbox=%s environment.\n Please verifiy calls should be limited.\nKind regards,\nChris.' % (threshold, self.sandbox) 
                send_mail.delay(sender, targets, subject, message)

                self.IexApiObject.messages_available = messages_available
                self.IexApiObject.save()

    # Set the sandbox environment, meaning we have to set the environment variable and download the new key
    def set_sandbox(self):
        os.environ['IEX_API_VERSION'] = 'iexcloud-sandbox'
        self.IexApiObject = IexApiKey.objects.filter(sandbox=True)[0]
        self.sandbox = True 

    # Unset the environment variable and get the main key
    def unset_sandbox(self):
        os.environ.pop('IEX_API_VERSION', None)
        self.IexApiObject = IexApiKey.objects.filter(sandbox=False)[0]
        self.sandbox = False 

    ## This function returns the following data:
    def query_key_stats(self):
        '''
            avg10Volume   # average 10 day volume   
            avg30Volume   # average 30 day volume 
            beta
            companyName   "Apple Inc."
            day200MovingAvg   140.60541,  # 200 day moving average
            day30ChangePercent
            day50MovingAvg    156.49678,   # 50 day moving average
            day5ChangePercent
            dividendYield     .021,  # The ratio of trailing twelve month dividend compared to the previous day close price. Dividends earned with respect to stock price. https://www.investopedia.com/terms/d/dividendyield.asp
            employees     120000,    # employees 
            exDividendDate 
            float  # just a return as of Dec 2020
            marketcap            760334287200
            maxChangePercent    # max change percent based on days
            month1ChangePercent   # change in 1 month
            month3ChangePercent    # change in 3 months 
            month6ChangePercent    # change in 6 months
            nextDividendDate    # next dividends
            nextEarningsDate    # next earnings
            peRatio             # Price to earnings ratio calculated as (previous day close price) / (ttmEPS)  https://www.investopedia.com/terms/p/price-earningsratio.asp
            sharesOutstanding  5213840000,  #  number of shares outstanding to calculate earnings per share  / an increase means company has less trust in itself https://www.investopedia.com/terms/o/outstandingshares.asp
            ttmDividendRate   2.25,    # Trailing twelve month dividend rate per share. Should be increasing as well
            ttmEPS    16.5,    # Trailing twelve month earnings per share. These should be increasing, otherwise the company is losing money. So look at trends as well here. https://www.investopedia.com/terms/t/trailingeps.asp
            week52change       # change in 52 weeks 
            week52high     156.65,  # high of the last 52 weeks
            week52low   93.63,  # low of the last 52 weeks
            year1ChangePercent   # change in 1 year 
            year2ChangePercent    # change in 2 years
            year5ChangePercent   # change in 5 years
            ytdChangePercent   # change this year

        cost: 5 per symbol apparently
        '''
         # Api only allows to call for 100 tickers at a time so split the call evenly
        for i in range(0, len(self.tickers), 100):
            current_tickers = self.tickers[i:i+100]
            stocks = iexfinance.stocks.Stock(current_tickers, token=self.IexApiObject.token)
            today = datetime.date.today()
            key_stats = stocks.get_key_stats(token=self.IexApiObject.token)
            for ticker, results in keys_stats.iterrows():
                for _, data in result.iterrows():

                    stock = Stock.objects.get(iexfinance_ticker=ticker)
                    # Delete existing entries
                    key_stats = KeyStats.objects.filter(stock=stock, date=today)
                    key_stats.delete()    

                    # And save the new entry
                    key_stats = KeyStats.objects.create(stock=stock,                
                        date = today,                                        
                        avg10Volume          = data['avg10Volume'],                       
                        avg30Volume          = data['avg30Volume'],                       
                        day200MovingAvg      = data['day200MovingAvg'],                       
                        day30ChangePercent   = data['day30ChangePercent'],                       
                        day50MovingAvg       = data['day50MovingAvg'],                       
                        day5ChangePercent    = data['day5ChangePercent'],                       
                        dividendYield        = data['dividendYield'],                       
                        employees            = data['employees'],                       
                        exDividendDate       = data['exDividendDate'],                       
                        marketcap            = data['marketcap'],                       
                        maxChangePercent     = data['maxChangePercent'],                       
                        month1ChangePercent  = data['month1ChangePercent'],                       
                        month3ChangePercent  = data['month3ChangePercent'],                       
                        month6ChangePercent  = data['month6ChangePercent'],                       
                        nextDividendDate     = data['nextDividendDate'],                       
                        nextEarningsDate     = data['nextEarningsDate'],                       
                        peRatio              = data['peRatio'],                       
                        sharesOutstanding    = data['sharesOutstanding'],                       
                        ttmDividendRate      = data['ttmDividendRate'],                       
                        ttmEPS               = data['ttmEPS'],                       
                        week52change         = data['week52change'],                       
                        week52high           = data['week52high'],                       
                        week52low            = data['week52low'],                       
                        year1ChangePercent   = data['year1ChangePercent'],                       
                        year2ChangePercent   = data['year2ChangePercent'],                       
                        year5ChangePercent   = data['year5ChangePercent'],                       
                        ytdChangePercent     = data['ytdChangePercent']                      
                    )             
        

    # Function to query the balance sheets 
    def query_balance_sheet(self):
        ''' 
        function returns 

            commonStock                    Number of shares outstanding as the difference between issued shares and treasury shares.
            currentAssets                  Represents cash and other assets that are reasonably expected to be realized in cash, sold or consumed within one year or one operating cycle. Generally, the sum of cash and equivalents, receivables, inventories, prepaid expenses, and other current assets. For non-U.S. companies, long term receivables are excluded from current assets even though included in net receivables. https://www.investopedia.com/terms/c/currentassets.asp
            currentCash                    Represents current cash excluding short-term investments. Current cash excludes commercial paper issued by unconsolidated subsidiaries to the parent company, amount due from sale of debentures, checks written by the company but not yet deposited and charged to the company’s bank account, and promissory notes.
            filingType                     Filing type
            fiscalDate                     The last day of the relevant fiscal period, formatted YYYY-MM-DD
            fiscalQuarter                  Associated fiscal quarter
            fiscalYear                     Associated fiscal year
            goodwill                       Represents the excess cost over the fair market value of the net assets purchased. Is excluded from other intangible assets.  https://www.investopedia.com/terms/g/goodwill.asp 
            intangibleAssets               Represents other assets not having a physical existence. The value of these assets lie in their expected future return. This excludes goodwill.  https://www.investopedia.com/ask/answers/013015/how-do-intangible-assets-appear-balance-sheet.asp
            inventory                      Represents tangible items or merchandise net of advances and obsolescence acquired for either resale directly or included in the production of finished goods manufactured for sale in the normal course of operation. Excludes tools that are listed in current assets, supplies and prepaid expenses for companies that lump these items together, advances from customers, and contract billings. For non-U.S. companies, if negative inventories arise from advances from customers greater than costs on long-term contracts, it is reclassified to current liabilities.
            longTermDebt                   Represents all interest-bearing financial obligations, excluding amounts due within one year, net of premium or discount. Excludes current portion of long-term debt, pensions, deferred taxes, and minority interest. https://www.investopedia.com/terms/l/longtermdebt.asp
            longTermInvestments            Represents total investments and advances for the period. Calculated as long term investment minus affiliate companies and other long term investments. https://www.investopedia.com/terms/l/longterminvestments.asp 
            minorityInterest               Represents the portion of earnings/losses of a subsidiary pertaining to common stock not owned by the controlling company or other members of the consolidated group. Minority Interest is subtracted from consolidated net income to arrive at the company’s net income.
            netTangibleAssets              Calculated as shareholder equity less goodwill and less
            otherAssets                    Returns other assets for the period calculated as other assets including intangibles minus intangible other assets.
            otherCurrentAssets             Represents other current assets for the period.  https://www.investopedia.com/terms/o/othercurrentassets.asp
            propertyPlantEquipment         Represents gross property, plant, and equipment less accumulated reserves for depreciation, depletion, and ammortization. https://www.investopedia.com/terms/p/ppe.asp 
            receivables                    Represents net claims against customers for merchandise sold or services performed in the ordinary course of business. https://www.investopedia.com/terms/n/netreceivables.asp
            reportDate                     Date financials were reported
            retainedEarnings               Represents the accumulated after tax earnings of the company which have not been distributed as dividends to shareholders or allocated to a reserve amount. Excess involuntary liquidation value over stated value of preferred stock is deducted if there is an insufficient amount in the capital surplus account. https://www.investopedia.com/terms/r/retainedearnings.asp
            shareholderEquity              Total shareholders’ equity for the period calculated as the sum of total common equity and preferred stock carrying value.
            totalAssets                    Represents the sum of total current assets, long-term receivables, investment in unconsolidated subsidiaries, other investments, net property plant and equipment, deferred tax assets, and other assets.
            totalCurrentLiabilities        Represents debt or other obligations that the company expects to satisfy within one year.
            totalLiabilities               Represents all short and long term obligations expected to be satisfied by the company. Excludes minority interest preferred stock equity, preferred stock equity, common stock equity, and non-equity reserves.
            treasuryStock                  Represents the acquisition cost of shares held by the company. For non-U.S. companies treasury stock may be carried at par value. This stock is not entitled to dividends, has no voting rights, and does not share in the profits in the event of liquidation. https://www.investopedia.com/terms/t/treasurystock.asp                    

        cost: 3000 per symbol
        '''
        # Api only allows to call for 100 tickers at a time so split the call evenly
        for i in range(0, len(self.tickers), 100):
            current_tickers = self.tickers[i:i+100]
            stocks = iexfinance.stocks.Stock(current_tickers, token=self.IexApiObject.token)
            today = datetime.date.today()
            balance_sheets = stocks.get_balance_sheet(token=self.IexApiObject.token)
            for ticker, result in balance_sheets.items():
                for _, data in result.iterrows():
                    stock = Stock.objects.get(iexfinance_ticker=ticker)
                    # Delete existing entries
                    balance_sheet = BalanceSheet.objects.filter(stock=stock, date=today)
                    balance_sheet.delete()

                    # And save the new data
                    balance_sheet = BalanceSheet.objects.create(stock = stock, 
                        date                    = today,
                        commonStock             = data['commonStock'],
                        currentAssets           = data['currentAssets'],
                        currentCash             = data['currentCash'],
                        fiscalDate              = data['fiscalDate'],
                        fiscalQuarter           = data['fiscalQuarter'],
                        fiscalYear              = data['fiscalYear'],
                        goodwill                = data['goodwill'],
                        intangibleAssets        = data['intangibleAssets'],
                        inventory               = data['inventory'],               
                        longTermDebt            = data['longTermDebt'],           
                        longTermInvestments     = data['longTermInvestments'],      
                        minorityInterest        = data['minorityInterest'],            
                        netTangibleAssets       = data['netTangibleAssets'],           
                        otherAssets             = data['otherAssets'],                
                        otherCurrentAssets      = data['otherCurrentAssets'],         
                        propertyPlantEquipment  = data['propertyPlantEquipment'], 
                        receivables             = data['receivables'],         
                        reportDate              = data['reportDate'],            
                        retainedEarnings        = data['retainedEarnings'],     
                        shareholderEquity       = data['shareholderEquity'],      
                        totalAssets             = data['totalAssets'],           
                        totalCurrentLiabilities = data['totalCurrentLiabilities'],
                        totalLiabilities        = data['totalLiabilities'],      
                        treasuryStock           = data['treasuryStock']
                    )


    # Function to query cash flow below
    def query_cash_flow(self):
        '''

            capitalExpenditures          Returns total capital expenditures for the period calculated as the sum of capital expenditures additions to fixed assets, and additions to other assets.
            cashFlow                     Returns net cash from operating activities for the period calculated as the sum of funds from operations, extraordinary items, and funds from other operating activities.
            cashFlowFinancing            Returns net cash from financing activities for the period.
            currency                     Currency code for reported financials.
            depreciation                 Depreciation represents the process of allocating the cost of a depreciable asset to the accounting periods covered during its expected useful life to a business. Depletion refers to cost allocation for natural resources such as oil and mineral deposits. Amortization relates to cost allocation for intangible assets such as patents and leasehold improvements, trademarks, book plates, tools & film costs. This item includes dry-hole expense, abandonments and oil and gas property valuation provision for extractive companies. This item excludes amortization of discounts or premiums on financial instruments owned or outstanding and depreciation on discontinued operations.
            filingType                   Filing type
            fiscalDate                   The last day of the relevant fiscal period, formatted YYYY-MM-DD
            fiscalQuarter                Associated fiscal quarter
            fiscalYear                   Associated fiscal year
            netIncome                    Represents income before extraordinary items and preferred and common dividends, but after operating and non-operating income and expenses, minority interest and equity in earnings.
            reportDate                   Date financials were reported.
            symbol                   
            totalInvestingCashFlows      Returns net cash from investing activities for the period calculated as (Cash Flow from Investing Activity) - Net. If this is not available, then it is calculated as (Other Uses/(Sources) Investing) + (Disposal of fixed assets) + (decrease in investments) - (net assets from acquisitions) - (capital expenditures other assets) - (increase in investments) - (capital expenditures additions to fixed assets)
            id                       
            key                      
            subkey                   
            updated                  

            cost: 1000 per symbol

        '''
        # Api only allows to call for 100 tickers at a time so split the call evenly
        for i in range(0, len(self.tickers), 100):
            current_tickers = self.tickers[i:i+100]
            stocks = iexfinance.stocks.Stock(current_tickers, token=self.IexApiObject.token)
            today = datetime.date.today()
            cash_flow = stocks.get_cash_flow(token=self.IexApiObject.token)
            for ticker, result in cash_flow.items():
                for _, data in result.iterrows():
                    stock = Stock.objects.get(iexfinance_ticker=ticker)
           
                    # Delete existing entries
                    cash_flow = CashFlow.objects.filter(stock=stock, date=today)
                    cash_flow.delete()

                    # And create a new entry
                    cash_flow = Cash_Flow.objects.create(stock = stock, 
                        date                    = today,
                        capitalExpenditures     = stats['capitalExpenditures'],
                        cashFlow                = stats['cashFlow'],
                        cashFlowFinancing       = stats['cashFlowFinancing'],
                        depreciation            = stats['depreciation'],
                        fiscalDate              = stats['fiscalDate'],
                        fiscalQuarter           = stats['fiscalQuarter'],
                        fiscalYear              = stats['fiscalYear'],
                        netIncome               = stats['netIncome'],
                        reportDate              = stats['reportDate'],
                        totalInvestingCashFlows = stats['totalInvestingCashFlows']
                    )



    # Functions to retireve income statement
    def query_income_statement(self):
        '''
        costOfRevenue               40939513908   Represents the cost of goods sold for the period including depletion and amortization. https://www.investopedia.com/terms/c/cost-of-revenue.asp
        currency                            USD   Currency code for reported financials.
        ebit                        15086191458   Represents operating income for the period calculated as (net sales or revenue) - (cost of goods sold) - (selling, general & administrative expenses) - (other operating expenses). This will only return for industrial companies. https://www.investopedia.com/terms/e/ebit.asp
        filingType                         1K0-   Filing type
        fiscalDate                   2020-09-12   The last day of the relevant fiscal period, formatted YYYY-MM-DD
        fiscalQuarter                         4   Associated fiscal quarter
        fiscalYear                         2118   Associated fiscal year
        grossProfit                 25281398992   Represents the difference between sales or revenues and cost of goods sold and depreciation.  https://www.investopedia.com/terms/g/grossprofit.asp
        incomeTax                    2247341422   Represents all income taxes levied on the income of a company by federal, state and foreign governments. Excludes domestic international sales corporation taxes, ad valorem taxes, excise taxes, windfall profit taxes, taxes other than income, and general and services taxes.
        interestIncome                646203185   Represents interest expense, net of interest capitalized for the period calculated as (interest expense on debt) - (interest capitalized) https://www.investopedia.com/terms/n/net-interest-income.asp
        minorityInterest                      0   Represents the portion of earnings/losses of a subsidiary pertaining to common stock not owned by the controlling company or other members of the consolidated group.
        netIncome                   12837247370   Represents income before extraordinary items and preferred and common dividends, but after operating and non-operating income and expenses, minority interest and equity in earnings. https://www.investopedia.com/terms/n/netincome.asp
        netIncomeBasic              12701038364   Represents net income available to common basic EPS before extraordinaries for the period calculated as (net income after preferred dividends) - (discontinued operations)
        operatingExpense            52306485544   Calculated as cost of revenue minus selling, general & administrative expense.  https://www.investopedia.com/terms/o/operating_expense.asp
        operatingIncome             15060681926   Represents operating income for the period calculated as (net sales or revenue) - (cost of goods sold) - (selling, general & administrative expenses) - (other operating expenses). This will only return for industrial companies.
        otherIncomeExpenseNet                 0   Calculated as income before tax minus operating income.
        pretaxIncome                15325718109   Represents all income/loss before any federal, state or local taxes. Extraordinary items reported net of taxes are excluded.
        reportDate                   2020-10-16   Date financials were reported.
        researchAndDevelopment       5116277367   Represents all direct and indirect costs related to the creation and development of new processes, techniques, applications and products with commercial possibilities. Excludes customer or government sponsored research, purchase of mineral rights (for oil, gas, coal, drilling and mining companies), engineering expense, and contributions by government, customers, partnerships or other corporations to the company’s research and development expense
        sellingGeneralAndAdmin       5181289905   Represents expenses not directly attributable to the production process but relating to selling, general and administrative functions. Excludes research and development.
        totalRevenue                66416868399   Refers to the sum of both operating and non-operating revenues . https://www.investopedia.com/terms/r/revenue.asp


        cost: 1000 per symbol
        '''
        # Api only allows to call for 100 tickers at a time so split the call evenly
        for i in range(0, len(self.tickers), 100):
            current_tickers = self.tickers[i:i+100]
            stocks = iexfinance.stocks.Stock(current_tickers, token=self.IexApiObject.token)
            today = datetime.date.today()
            income_statement = stocks.get_income_statement(token=self.IexApiObject.token)
            for ticker, result in income_statement.items():
                for _, data in result.iterrows():
                    stock = Stock.objects.get(iexfinance_ticker=ticker)

                    # Delete existing entries
                    income_statement = IncomeStatement.objects.filter(stock=stock, date=today)
                    income_statement.delete()

                    # And create a new entry
                    income_statement = IncomeStatement.objects.create(stock = stock, 
                        date = today,
                        costOfRevenue           = stats['costOfRevenue'],
                        ebit                    = stats['ebit'],
                        fiscalDate              = stats['fiscalDate'],
                        fiscalQuarter           = stats['fiscalQuarter'],
                        fiscalYear              = stats['fiscalYear'],
                        grossProfit             = stats['grossProfit'],
                        incomeTax               = stats['incomeTax'],
                        interestIncome          = stats['interestIncome'],
                        minorityInterest        = stats['minorityInterest'],
                        netIncome               = stats['netIncome'],
                        netIncomeBasic          = stats['netIncomeBasic'],
                        operatingExpense        = stats['operatingExpense'],
                        operatingIncome         = stats['operatingIncome'],
                        otherIncomeExpenseNet   = stats['otherIncomeExpenseNet'],
                        pretaxIncome            = stats['pretaxIncome'],
                        reportDate              = stats['reportDate'],
                        researchAndDevelopment  = stats['researchAndDevelopment'], 
                        sellingGeneralAndAdmin  = stats['sellingGeneralAndAdmin'], 
                        totalRevenue            = stats['totalRevenue']
                    )
    
        
