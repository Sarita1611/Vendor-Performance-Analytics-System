import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

import seaborn as sns
import warnings
import sqlite3
from scipy.stats import ttest_ind
import scipy.stats as stats
warnings.filterwarnings('ignore')

#loading the dataset

#creating the database connection
conn=sqlite3.connect('inventory.db')

# fetching the vendor summary data
df=pd.read_sql_query('select * from vendor_sales_summary',conn)
print(df.head())

# EXPLORATRY DATA ANALYSIS
"""
-> previusly we examined the various tables in database to identify key variables, understand their relationships, and determine which ones 
   should be included in the final analysis
-> IN this phase of EDA, we will analyze the resultant table to gain insights into the distribution of each column. this will help us understand
data patterns, identify anomalies, and ensure quanlity before proceeding with further analysis
"""
# summary statistics
print(df.describe().T)


#Distribution plots for numerical columns
numerical_cols=df.select_dtypes(include=np.number).columns

plt.figure(figsize=(15,10))
for i,col in enumerate(numerical_cols):
    plt.subplot(4,4,i+1)
    sns.histplot(df[col],kde=True,bins=30)
    plt.title(col)
plt.tight_layout()
plt.show()


plt.figure(figsize=(15,10))
for i,col in enumerate(numerical_cols):
    plt.subplot(4,4,i+1)
    sns.boxplot(df[col])
    plt.title(col)
plt.tight_layout()
plt.show()

#Summary stats insights
"""
Negative and zero values
-> gross profit: minimum value id -52002.78 indicating losses. some product r transactions may be selling at a loss due to high costs or 
   selling at loss due to high costs or selling at discounts lower than the purchase rate
-> profit margin: has a minimum of -infinity. which suggests cases where revenue is zero or even lower than costs.
-> total sales quantity and sales dollars: minimum values are 0, meaning some products were purchaesd but were never sold. these could be 
   slow moving or obsolete stock

Outliers indicated by high standard deviations:
-> purchase and actual prices: the max values (5681.81& 7499.99) are significantly higher then the mean(24.39 & 35.64), indicating otential 
   premium products.
-> freight cost: huge variation, from 0.09 to 257032.07, suggests logistics inefficies or bulk shipments. 
-> stock turnover: ranges from 0 to 274.5 implying some products sell extremely fast while others remain in stock indefinetly, value more than 1 
   indicates that sold quantity forthat product is higher than purchased quantity due to either sales are being fullfilled from older stock 
"""
df=pd.read_sql_query("""SELECT * FROM vendor_sales_summary WHERE GrossProfit>0 and ProfitMargin>0 AND TotalSalesQuantity>0
""",conn)
print(df)

numerical_cols=df.select_dtypes(include=np.number).columns
plt.figure(figsize=(15,10))
for i,col in enumerate(numerical_cols):
    plt.subplot(4,4,i+1)
    sns.histplot(df[col],kde=True,bins=30)
    plt.title(col)
plt.tight_layout()
plt.show()

categorical_cols=['VendorName','Description']
plt.figure(figsize=(15,10))
for i,col in enumerate(categorical_cols):
    plt.subplot(4,4,i+1)
    sns.countplot(y=df[col],order=df[col].value_counts().index[:10])
    plt.title(f"count plot of {col}")
plt.tight_layout()
plt.show()



#correlatin heatmap
plt.figure(figsize=(12,8))
correlation_matrix=df[numerical_cols].corr()
sns.heatmap(correlation_matrix,annot=True,fmt=".2f",cmap="coolwarm",linewidths=0.5)
plt.title("correlation heatmap")
plt.show()


#correlatin insights
"""
-> purchaseprice has week correlation with totalsalesdollars(-0.012) and grossprofit(-0.016), suggesting that price variations do not 
   significantly impact sales revenue or profit.
-> strong correlation between total purchase quantity and total sales quantity(0.999), conforming efficient inventory turnover.
-> negative correlation between profit margin and ttal sales price(-0.179) suggests that as sales price increases, margin decreases ,
   possibly due to competetive pricing pressures.
-> stockturnover has weak negative correlatios with both grossprofit(-0.038) and profitmargin(-0.055), indicating that faster turnover doesnot 
   necessarily result in higher profitability.
"""

#DATA ANALYSIS 
"""
identify brandsthat needs promotional or pricing adjustments which exhibit lower sales performance but higher profit margins
"""
brand_performance=df.groupby('Description').agg({
    'TotalSalesDollars':"sum",
    'ProfitMargin':'mean'
}).reset_index()

low_sales_threshold=brand_performance['TotalSalesDollars'].quantile(0.15)
high_margin_threshold=brand_performance['ProfitMargin'].quantile(0.85)
print(low_sales_threshold)
print(high_margin_threshold)

#filter brands with low sales but high performance margin
target_brands=brand_performance[(brand_performance['TotalSalesDollars']<=low_sales_threshold) &
                                (brand_performance['ProfitMargin']>=high_margin_threshold)]
print("brands with lower sales but high profit margins")
print(target_brands.sort_values('TotalSalesDollars'))

brand_performance=brand_performance[brand_performance['TotalSalesDollars']<10000] # for better visualization
plt.figure(figsize=(10,6))
sns.scatterplot(data=brand_performance,x='TotalSalesDollars',y='ProfitMargin',color='blue',label='All Brands',alpha=0.2)
sns.scatterplot(data=target_brands,x='TotalSalesDollars',y='ProfitMargin',color='red',label='Target Brands')

plt.axhline(high_margin_threshold,linestyle="--",color='black',label="High Margin Threshold")
plt.axvline(low_sales_threshold,linestyle="--",color='black',label="low_sales_threshold")

plt.xlabel("Total Sales ($)")
plt.ylabel("Profit margin (%)")
plt.title("brands for promotional or pricing adjustments")
plt.legend()
plt.grid(True)
plt.show()
def format_dollars(value):
    if value>=1_000_000:
        return f"{value/1_000_000:.2f}M"
    elif value>=1_000:
        return f"{value/1_000:2f}K"
    else:
        return str(value)
   
# Next business question which vendors and brands demonstrate the highest sales performance?
#top vendors and brands by sales performance
top_vendors=df.groupby("VendorName")["TotalSalesDollars"].sum().nlargest(10)
top_brands=df.groupby("Description")['TotalSalesDollars'].sum().nlargest(10)
print(top_vendors)
print(top_brands)
top_brands.apply(lambda x: format_dollars(x))
print(top_brands)

#using bar plot
plt.figure(figsize=(15,5))
#plot for top vendors
plt.subplot(1,2,1)
ax1=sns.barplot(y=top_vendors.index,x=top_vendors.values,palette="Blues_r")
plt.title("top 10 Vendors by sales ")

for bar in ax1.patches:
    ax1.text(bar.get_width()+(bar.get_width()*0.02),
             bar.get_y()+bar.get_height()/2,
             format_dollars(bar.get_height()),
             ha="left",va='center',fontsize=10,color='black')
    
#plot for top brands
plt.subplot(1,2,2)
ax2=sns.barplot(y=top_brands.index.astype(str),x=top_brands.values,palette="Reds_r")
plt.title("top 10 Brands by sales ")

for bar in ax2.patches:
    ax1.text(bar.get_width()+(bar.get_width()*0.02),
             bar.get_y()+bar.get_height()/2,
             format_dollars(bar.get_height()),
             ha="left",va='center',fontsize=10,color='black')
plt.tight_layout()
plt.show()

#Which vendors contribute the most to total purchased dollars?
vendor_performance=df.groupby("VendorName").agg({
    'TotalPurchaseDollars':'sum',
    "GrossProfit":"sum",
    'TotalSalesDollars':'sum'
}).reset_index()

vendor_performance['PurchaseContribution%']=vendor_performance['TotalPurchaseDollars']/vendor_performance['TotalPurchaseDollars'].sum()*100
vendor_performance=round(vendor_performance.sort_values('PurchaseContribution%',ascending=False),2)

#Display top 10 Vendors
top_vendors=vendor_performance.head(10)
top_vendors['TotalSalesDollars']=top_vendors['TotalSalesDollars'].apply(format_dollars)
top_vendors['TotalPurchaseDollars']=top_vendors['TotalPurchaseDollars'].apply(format_dollars)
top_vendors['GrossProfit']=top_vendors['GrossProfit'].apply(format_dollars)
print(top_vendors)
print(top_vendors['PurchaseContribution%'].sum())

top_vendors['Cumulative_Contribution']=top_vendors['PurchaseContribution%'].cumsum()
print(top_vendors)

fig,ax1=plt.subplots(figsize=(10,6))
#bar plot for purchase contribution%
sns.barplot(x=top_vendors['VendorName'],y=top_vendors['PurchaseContribution%'],palette='mako',ax=ax1)
for i,value in enumerate(top_vendors['PurchaseContribution%']):
    ax1.text(i,value-1,str(value)+'%',ha='center',fontsize=10,color='white')

#line plot for cumulative contribution%
ax2=ax1.twinx()
ax2.plot(top_vendors['VendorName'],top_vendors['Cumulative_Contribution'],color='red',marker='o',linestyle='dashed',label='cumulative')

ax1.set_xticklabels(top_vendors['VendorName'],rotation=90)
ax1.set_ylabel('Purchase Contribution %',color='blue')
ax2.set_ylabel('Cumulative Contribution %',color='red')
ax1.set_xlabel('Vendors')
ax1.set_title('pareto chart:Vendor contribution to total purchases')

ax2.axhline(y=100,color='gray',linestyle='dashed',alpha=0.7)
ax2.legend(loc='upper right')

plt.show()

#how much of total procurement is dependent on the top vendors?
print(f"total purchase contribution of top 10 vendors is {round(top_vendors)['PurchaseContribution%'].sum(),2}%")

vendors=list(top_vendors['VendorName'].values)
purchase_contributions=list(top_vendors['PurchaseContribution%'].values)
total_contribution=sum(purchase_contributions)
remaining_contributions=100-total_contribution

#append other vendors category 
vendors.append('Other Vendors')
purchase_contributions.append(remaining_contributions)

#Donut chart 
fig,ax=plt.subplots(figsize=(8,8))
wedges,texts,autotexts=ax.pie(purchase_contributions,labels=vendors,autopct='%1.1f%%',
                              startangle=140,pctdistance=0.05,colors=plt.cm.Paired.colors)

##draw a white circle in the center to create a "donut " effect 
centre_circle=plt.Circle((0,0),0.70,fc='white')
fig.gca().add_artist(centre_circle)

#add total contributions annotation in the center
plt.text(0,0,f"top 10 :\n{total_contribution:.2f}%",fontsize=14,fontweight='bold',ha='center',va='center')

plt.title("top 10 vendor's  purchase contribution (%)")
plt.show()

# DOES PURCHASING IN BULK REDUCE THE UNIT PRICE AND WHAT IS THE OPTIMAL PURCHASE VOLUME FOR COST SAVINGS?
df['UnitPurchasePrice']=df['TotalPurchaseDollars']/df['TotalPurchaseQuantity']
df['OrderSize']=pd.qcut(df['TotalPurchaseQuantity'],q=3,labels=['Small','Medium','Large'])
print(df[['OrderSize','TotalPurchaseQuantity']])
df.groupby('OrderSize')[['UnitPurchasePrice']].mean()

plt.figure(figsize=(10,6))
sns.boxplot(data=df,x='OrderSize',y='UnitPurchasePrice',palette='Set2')
plt.title('Impact of bulk purchasing on unit price')
plt.xlabel('order size')
plt.ylabel('average unit purchase price')
plt.show()

"""
-> vendors buying in bulk (large order size) get the lowest unit price ($10.78 per unit), meaing higher margins if they can manage inventory
   efficiently
-> the price difference between small and large orders is substantial (~72% reduction in unit cost)
-> this suggest that bulk pricing staregies succesfully encourage vendors to purchase in larger volumes, leading to higher overall sales despite 
   lower per unit revenue
"""

#WHICH VENDOR HAVE LOW INVENTORY TURNOVER, INDICATIONG EXCESS STOCK AND SLOW-MOVING PRODUCTS?
df[df['StockTurnover']<1].groupby('VendorName')[['StockTurnover']].mean().sort_values('StockTurnover',ascending=True).head(10)

#HOW MUCH CAPITAL IS LOCKED IN UNSOLD INVENTORY PER VENDOR, AND WHICH VENDORS CONTRIBUTE THE MOST TO IT?
df['UnsoldInventoryValue']=(df['TotalPurchaseQuantity']-df['TotalSalesQuantity'])*df['PurchasePrice']
print('Total Unsold Capital:',format_dollars(df['UnsoldInventoryValue'].sum()))

#Aggregate capital locked per vendor
inventory_value_per_vendor=df.groupby('VendorName')['UnsoldInventoryValue'].sum().reset_index()

#sort vendors with the highest locked capital
inventory_value_per_vendor=inventory_value_per_vendor.sort_values(by='UnsoldInventoryValue',ascending=False)
inventory_value_per_vendor['UnsoldInventory']=inventory_value_per_vendor['UnsoldInventoryValue'].apply(format_dollars)
print(inventory_value_per_vendor.head(10))

#WHAT IS THE 95%CONFIDENCE INTERVALS FOR PROFIT MARGINS OF TOP PERFORMING AND LOW PERFORMING VENDORS
top_threshold=df['TotalSalesDollars'].quantile(0.75)
low_threshold=df['TotalSalesDollars'].quantile(0.25)
top_vendors=df[df['TotalSalesDollars']>=top_threshold]['ProfitMargin'].dropna()
low_vendors=df[df['TotalSalesDollars']<=low_threshold]['ProfitMargin'].dropna()
print(top_vendors)

def confidence_interval(data,confidence=0.95):
    mean_val=np.mean(data)
    std_err=np.std(data,ddof=1)/np.sqrt(len(data))
    t_critical=stats.t.ppf((1+confidence)/2,df=len(data)-1)
    margin_of_error=t_critical*std_err
    return mean_val,mean_val-margin_of_error,mean_val+margin_of_error


top_mean,top_lower,top_upper=confidence_interval(top_vendors)
low_mean,low_lower,low_upper=confidence_interval(low_vendors)

print(f"top vendors 95% CI: ({top_lower:.2f},{top_upper:.2f},Mean:{top_mean:.2f})")
print(f'low vendors 95% CI: ({low_lower:.2f},{low_upper:.2f},Mean:{low_mean:.2f})')

plt.figure(figsize=(12,6))

#Top vendors plot
sns.histplot(top_vendors,kde=True,color='blue',bins=30,alpha=0.5,label='top vendors')
plt.axvline(top_lower,color='blue',linestyle="--",label=f"Top Lower: {top_lower:.2f}")
plt.axvline(top_upper,color='blue',linestyle="--",label=f"Top Lower: {top_upper:.2f}")
plt.axvline(top_mean,color='blue',linestyle="--",label=f"Top Lower: {top_mean:.2f}")

#low vendors plot
sns.histplot(low_vendors,kde=True,color='red',bins=30,alpha=0.5,label='low vendors')
plt.axvline(low_lower,color='blue',linestyle="--",label=f"Top Lower: {low_lower:.2f}")
plt.axvline(low_upper,color='blue',linestyle="--",label=f"Top Lower: {low_upper:.2f}")
plt.axvline(low_mean,color='blue',linestyle="--",label=f"Top Lower: {low_mean:.2f}")

#finalize plot
plt.title("confidence interval comparison: top vs low vendors( profit margin)")
plt.xlabel('profit margin (%)')
plt.ylabel('frequency')
plt.legend()
plt.grid(True)
plt.show()


"""
-> the confidence interval for low performing vendors (40.48% to 42.62%) is significantly higher than that of top performing vendors (30.74 % to 31.60%)
-> this suggests that vendors with lower sales tend to maintain higher profit margins, potentially due to premium pricing or lower operatioal costs.
-> for high performing vendors: if they aim to improve profitability, they could explore selective price adjustments, cost optimization, or bundling strategies.
-> for low performing vendors: Despite higher margins, their low sales volume might indicate a need for better marketing, competitive pricing, or improved
   distribution strategies

"""

#IS THERE A SIGNIFICANT DIFFERENCE IN PROFIT MARGINS BETWEEN TOP PERFORMING AND LOW PERFORMING VENDORS?
# HYPOTHESIS:
"""
H0(NULL HYPOTHESIS): there is no significant difference in the mean profit margins of top performing and low performing vendors.
H1(Alternate Hypothesis): the mean profit margins of top performing and low performing vendors are significanlty different
"""

top_threshold=df['TotalSalesDollars'].quantile(0.75)
low_threshold=df['TotalSalesDollars'].quantile(0.25)
top_vendors=df[df['TotalSalesDollars']>=top_threshold]['ProfitMargin'].dropna()
low_vendors=df[df['TotalSalesDollars']<=low_threshold]['ProfitMargin'].dropna()

#perform two-sample T-Test
t_start,p_value=ttest_ind(top_vendors,low_vendors,equal_var=False)

#print results
print(f"T-Statistics:{t_start:.4f},p_value:{p_value}")
if p_value<0.05:
    print('reject h0: there is a significantly difference in the profit margins between top and low-performing vendors')
else:
    print("fail to reject h0: No significant difference in profit margins")
    