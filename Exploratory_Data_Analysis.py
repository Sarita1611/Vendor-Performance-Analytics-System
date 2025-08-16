"""Understanding the data to explore how the data is present in the database and if there is need ofcreating some aggregated tables that can help with :
   -> vendor selection for profitability 
   -> Product Pricing Optimization
"""
import pandas as pd
import sqlite3
#creating database connection
conn=sqlite3.connect('inventory.db')

#checking tables present in database
tables=pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'",conn)
# Print the list of tables
print("Tables in inventory.db:")
print(tables)

for table in tables['name']:
   print("-"*50, f"{table}","-"*50)
   print("Count of records:", pd.read_sql(f"SELECT count(*) as count FROM {table}",conn)['count'].values[0])
   print(pd.read_sql(f"SELECT * FROM {table} limit 5", conn))
print("---------------------")
purchases=pd.read_sql_query("SELECT *  from purchases where VendorNumber=4466",conn)
print(purchases) 
print("---------------------")
purchase_prices=pd.read_sql_query("SELECT * FROM purchase_prices WHERE VendorNumber=4466",conn)
print(purchase_prices)
print("---------------------")
vendor_invoice=pd.read_sql_query("SELECT * FROM vendor_invoice WHERE VendorNumber=4466",conn)
print(vendor_invoice)
print("---------------------")
sales=pd.read_sql_query("SELECT * FROM sales WHERE VendorNo=4466",conn)
print(sales)

purchases.groupby(['Brand','PurchasePrice'])[['Quantity','Dollars']].sum()
sales.groupby('Brand')[['SalesDollars', 'SalesPrice','SalesQuantity']].sum()
"""
->The purchases table contains actual purchase data, including the date of purchase, product (brands) purchased by vendors , the amunt paid
(in dollars) and the quantity purchased
->The purchase price column is derived from purchase_prices table , which provides product wise actual and purchase prices. The combinatin
of vendor and brand is unique in the table.
->The vendor_invoice table aggregates data from purchases table, summarizing quantity and dollar amounts, along with the additinal column
for freight. this table maintains uniqueness based on vendor and PO number
->The sales table captures actual sales transactions,detailing the brands purchased by vendors, the quantity sold, the selling price, 
and the revenue earned.

"""
"""
As the data that we need for analysis is distributed in different tables, we need to create a summary table containing:
 ->purchase transaction made by vendors
 ->sales Transaction data 
 ->freight costs for each vendor
 ->actual product prices from vendor
"""
# """
# freight_summary=pd.read_sql_query("""Select VendorNumber , SUM(Freight) as freightcost
#                                   FROM vendor_invoice
#                                   GROUP BY VendorNumber""",conn)
# print(freight_summary)

# pd.read_sql_query("""SELECT p.VendorName,
#                   p.VendorNumber,
#                   p.Brand,
#                   p.PurchasePrice,
#                   pp.Volume,
#                   pp.Price as ActualPrice,
#                   SUM(p.Quantity) as TotalPurchaseQuantity,
#                   SUM(p.Dollars) as TotalPurchaseDollars
#                   FROM purchases p
#                   JOIN purchase_prices pp
#                   ON p.Brand=pp.Brand
#                   WHERE p.PurchasePrice>0
#                   GROUP BY p.VendorName, p.VendorNumber, p.Brand
#                   ORDER BY TotalPurchaseDollars

# """,conn)


# pd.read_sql_query("""SELECT 
#                   VendorNo,
#                   Brand,
#                   SUM(SalesDollars) as TotalSalesDollars,
#                   SUM(SalesQuantity) as TotalSalesQuantity,
#                   SUM(ExciseTax) as TotalExciseTax
#                   FROM sales
#                   GROUP BY VendorNo, Brand
#                   ORDER BY TotalSalesDollars""",conn)
# """

##Final query to join all the three tables
# import time
# start=time.time()
# print(final_table=pd.read_sql_query("""SELECT 
#                               pp.VendorName,
#                               pp.brand,
#                               pp.Price AS ActualPrice,
#                               pp.PurchasePrice,
#                               Sum(s.SalesQuantity) AS TotalSalesQuantity,
#                               SUM(s.SalesDollars) AS TotalSalesDollars,
#                               Sum(s.SalesPrice) AS TotalSalesPrice,
#                               SUM(s.ExciseTax) AS TotalExciseTax,
#                               SUM(vi.Quantity) AS TotalPurchaseQuantity,
#                               SUM(vi.Dollars) AS TotalPurchaseDollars,
#                               SUM(vi.Freight) AS TotalFreightCost
#                               FROM purchase_prices pp
#                               JOIN sales s
#                               ON pp.VendorNumber=s.VendorNo
#                               AND pp.brand=s.brand
#                               JOIN vendor_invoice vi
#                               ON pp.VendorNumber=vi.VendorNumber
#                               GROUP BY pp.VendorNumber,pp.Brand,pp.Price,pp.PurchasePrice
# """,conn))
# end=time.time()


vendor_sales_summary = pd.read_sql_query("""
WITH 
FreightSummary AS (
    SELECT 
        VendorNumber,
        SUM(Freight) AS FreightCost
    FROM vendor_invoice
    GROUP BY VendorNumber
),
PurchaseSummary AS (
    SELECT 
        p.VendorNumber,
        p.VendorName,
        p.Brand,
        p.Description,
        p.PurchasePrice,
        pp.Price AS ActualPrice,
        pp.Volume,
        SUM(p.Quantity) AS TotalPurchaseQuantity,
        SUM(p.Dollars) AS TotalPurchaseDollars
    FROM purchases p
    JOIN purchase_prices pp ON p.Brand = pp.Brand
    WHERE p.PurchasePrice > 0
    GROUP BY 
        p.VendorNumber, 
        p.VendorName, 
        p.Brand, 
        p.Description, 
        p.PurchasePrice, 
        pp.Price, 
        pp.Volume
),
SalesSummary AS (
    SELECT 
        VendorNo,
        Brand,
        SUM(SalesQuantity) AS TotalSalesQuantity,
        SUM(SalesDollars) AS TotalSalesDollars,
        SUM(SalesPrice) AS TotalSalesPrice,
        SUM(ExciseTax) AS TotalExciseTax
    FROM sales
    GROUP BY VendorNo, Brand
)

SELECT 
    ps.VendorNumber,
    ps.VendorName,
    ps.Brand,
    ps.Description,
    ps.PurchasePrice,
    ps.ActualPrice,
    ps.Volume,
    ps.TotalPurchaseQuantity,
    ps.TotalPurchaseDollars,
    ss.TotalSalesQuantity,
    ss.TotalSalesDollars,
    ss.TotalSalesPrice,
    ss.TotalExciseTax,
    fs.FreightCost
FROM PurchaseSummary ps
LEFT JOIN SalesSummary ss 
    ON ps.VendorNumber = ss.VendorNo AND ps.Brand = ss.Brand
LEFT JOIN FreightSummary fs 
    ON ps.VendorNumber = fs.VendorNumber
ORDER BY ps.TotalPurchaseDollars DESC
""", conn)
print(vendor_sales_summary)

"""
This query generate a verndor wise sales and purchase summary, which is valuable for
PERFORMANCE OPTIMIZATION:
->this query involves heavy joins and aggregations on large datasets like sales and purchases
->storing the pre-aggregated result avoids expensive computations.
->helps in analyzing sales, purchases and pricing for different vendors and brands
->future benefits of storing this data for faster dashboarding and reporting 
->instead of running expensive queries each time, dashbards can fetch data quickly from vendor_sales_summary.

"""
print(vendor_sales_summary.dtypes)
print(vendor_sales_summary.isnull().sum())

print(vendor_sales_summary.head)

print(vendor_sales_summary['Description'].unique())
vendor_sales_summary['Volume']=vendor_sales_summary['Volume'].astype('float64')
vendor_sales_summary.fillna(0,inplace=True)
vendor_sales_summary['VendorName']=vendor_sales_summary['VendorName'].str.strip()
print(vendor_sales_summary["VendorName"].unique())
print(vendor_sales_summary.dtypes)
vendor_sales_summary['GrossProfit']=vendor_sales_summary['TotalSalesDollars']-vendor_sales_summary['TotalPurchaseDollars']
print(vendor_sales_summary['GrossProfit'].min())
vendor_sales_summary['ProfitMargin']=(vendor_sales_summary['GrossProfit']/vendor_sales_summary['TotalSalesDollars'])*100
vendor_sales_summary['StockTurnover']=vendor_sales_summary['TotalSalesQuantity']/vendor_sales_summary['TotalPurchaseQuantity']
vendor_sales_summary['SalesToPurchaseRatio']=vendor_sales_summary['TotalSalesDollars']/vendor_sales_summary['TotalPurchaseDollars']
print(vendor_sales_summary)
cursor=conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS vendor_sales_summary (
    VendorNumber INT,
    VendorName VARCHAR(100),
    Brand INT,
    Description VARCHAR(100),
    PurchasePrice DECIMAL(10,2),
    ActualPrice DECIMAL(10,2),
    Volume INT,
    TotalPurchaseQuantity INT,
    TotalPurchaseDollars DECIMAL(15,2),
    TotalSalesQuantity INT,
    TotalSalesDollars DECIMAL(15,2),
    TotalSalesPrice DECIMAL(15,2),
    TotalExciseTax DECIMAL(15,2),
    FreightCost DECIMAL(15,2),
    GrossProfit DECIMAL(15,2),
    ProfitMargin DECIMAL(15,2),
    StockTurnover DECIMAL(15,2),
    SalesToPurchaseRatio DECIMAL(15,2),
    PRIMARY KEY (VendorNumber, Brand)
);
""")

print(pd.read_sql_query("SELECT * FROM vendor_sales_summary",conn))
vendor_sales_summary.to_sql('vendor_sales_summary',conn, if_exists='replace',index=False)
print(pd.read_sql_query("SELECT * FROM vendor_sales_summary",conn))