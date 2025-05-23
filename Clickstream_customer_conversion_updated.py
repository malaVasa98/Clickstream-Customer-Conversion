# Import librarires
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

st.title(":green[CLICKSTREAM CUSTOMER CONVERSION]")
st.write("In this app, the user can upload a csv file consisting of clickstream data, and can get the relevant details like customers who will purchase or not, total revenue generated by the customer, and segmentation of customers into distinct groups based on their online behavior patterns.")
uploaded_file = st.file_uploader("Upload your file",type=["csv"])

if uploaded_file is not None:
    test_click = pd.read_csv(uploaded_file)
    st.success("File uploaded sucessfully")
    if st.button("Run app"):
        test_click['order_log'] = np.log1p(test_click['order'])
        
        # Regression - To predict price
        # Load the pipeline
        regress_pipeline = joblib.load("Regression_pipeline.pkl")
        
        test_click_regress = test_click.drop(['year','order','session_id','page2_clothing_model'],axis=1)
        X_unk = test_click_regress.copy()
        Pred_price = regress_pipeline.predict(X_unk)
        test_click['price'] = Pred_price
        
        # Classification - to predict whether purchase is completed or not
        test_click_class = test_click.drop(['year','order','session_id','page2_clothing_model'],axis=1)
        test_click_class = test_click_class[['month','day','country','page1_main_category','colour','location','model_photography',
                                             'price','page','order_log']]
        # Load the pipeline
        classify_pipeline = joblib.load("Classification_pipeline.pkl")
        X_cl_unk = test_click_class.copy()
        Pred_price_2 = classify_pipeline.predict(X_cl_unk)
        test_click['price_2'] = Pred_price_2
        test_click.price_2 = test_click.price_2.map({1:1,0:2})
        
        st.write(":blue[Customers who will make a purchase]")
        buy_df = test_click[test_click.price_2==1]
        st.dataframe(buy_df)
        st.write(f"{len(buy_df)} customers will make a purchase")
        
        clicks_per_session = buy_df.groupby("session_id")["order"].max()
        bounced_sessions = clicks_per_session[clicks_per_session == 1]
        bounce_rate = len(bounced_sessions) / len(clicks_per_session)
        st.write(f"**Bounce Rate**: {bounce_rate:.2%}")
        
        def has_revisit(group):
            return group["page"].duplicated().any()

        revisit_sessions = buy_df.groupby("session_id").apply(has_revisit)

        revisit_rate = revisit_sessions.sum() / revisit_sessions.count()
        st.write(f"**Revisit Rate**: {revisit_rate:.2%}")
        
        st.write(":blue[Customers who won't make a purchase]")
        not_buy_df = test_click[test_click.price_2==2]
        st.dataframe(not_buy_df)
        st.write(f"{len(not_buy_df)} customers won't make a purchase")
        
        clicks_per_session = not_buy_df.groupby("session_id")["order"].max()
        bounced_sessions = clicks_per_session[clicks_per_session == 1]
        bounce_rate = len(bounced_sessions) / len(clicks_per_session)
        st.write(f"**Bounce Rate**: {bounce_rate:.2%}")
        
        def has_revisit(group):
            return group["page"].duplicated().any()

        revisit_sessions = not_buy_df.groupby("session_id").apply(has_revisit)

        revisit_rate = revisit_sessions.sum() / revisit_sessions.count()
        st.write(f"**Revisit Rate**: {revisit_rate:.2%}")
        
        st.write(f":red[Revenue]")
        revenue_tot = test_click[['price']][test_click['price_2']==1].sum()
        st.write(f"**Total revenue generated**: ${revenue_tot.iloc[0]}")
        
        # Clustering - Task
        test_click_clus = test_click.copy()
        test_click_clus.drop('order',axis=1,inplace=True)
        # For clustering, groupby based on session_id
        test_click_clus['date'] = pd.to_datetime(dict(year=test_click_clus.year,
                                                          month=test_click_clus.month,
                                                          day=test_click_clus.day))
        cluster_click_unk = test_click_clus.groupby('session_id').agg({
            'date': lambda x: x.mode().iloc[0],
            'price': 'mean',
            'page': 'median',
            'order_log': 'median',
            'country': lambda x: x.mode().iloc[0],
            'page1_main_category': lambda x: x.mode().iloc[0],
            'colour': lambda x: x.mode().iloc[0],
            'location': lambda x: x.mode().iloc[0],
            'model_photography': lambda x: x.mode().iloc[0],
            'price_2': lambda x: x.mode().iloc[0],
        })
        
        cluster_click_unk['month'] = cluster_click_unk['date'].dt.month
        cluster_click_unk['day'] = cluster_click_unk['date'].dt.day
        cluster_click_unk.drop('date',axis=1,inplace=True)
        clicks_per_session = test_click_clus.groupby("session_id")["order_log"].max()
        clicks_per_session = pd.DataFrame(clicks_per_session)
        clicks_per_session = clicks_per_session.rename(columns={'order_log':'clicks_per_session'})
        cluster_click_unk = pd.concat([cluster_click_unk,clicks_per_session],axis=1)
        
        # Load the pipeline
        cluster_pipeline = joblib.load("Cluster_pipeline.pkl")
        
        # Cluster on unknown data 
        labels_unk = cluster_pipeline.predict(cluster_click_unk)
        cluster_click_unk['Cluster_groups'] = labels_unk
        
        cluster_summ = cluster_click_unk.copy()
        # Rename the labels of categorical features
        country_mapping = {
            1:"Australia",
            2:"Austria",
            3:"Belgium",
            4:"British Virgin Islands",
            5:"Cayman Islands",
            6:"Christmas Island",
            7:"Croatia",
            8:"Cyprus",
            9:"Czech Republic",
            10:"Denmark",
            11:"Estonia",
            12:"unidentified",
            13:"Faroe Islands",
            14:"Finland",
            15:"France",
            16:"Germany",
            17:"Greece",
            18:"Hungary",
            19:"Iceland",
            20:"India",
            21:"Ireland",
            22:"Italy",
            23:"Latvia",
            24:"Lithuania",
            25:"Luxembourg",
            26:"Mexico",
            27:"Netherlands",
            28:"Norway",
            29:"Poland",
            30:"Portugal",
            31:"Romania",
            32:"Russia",
            33:"San Marino",
            34:"Slovakia",
            35:"Slovenia",
            36:"Spain",
            37:"Sweden",
            38:"Switzerland",
            39:"Ukraine",
            40:"United Arab Emirates",
            41:"United Kingdom",
            42:"USA",
            43:"biz (.biz)", 
            44:"com (.com)",
            45:"int (.int)", 
            46:"net (.net)",
            47:"org (*.org)"
        }
        # Replace country 
        cluster_summ.country = cluster_summ.country.replace(country_mapping)
        
        product_category = {
            1:"trousers",
            2:"skirts",
            3:"blouses",
            4:"sale"
        }
        # Product category
        cluster_summ.page1_main_category = cluster_summ.page1_main_category.replace(product_category)
        
        color_mapping = {
            1:"beige",
            2:"black",
            3:"blue",
            4:"brown",
            5:"burgundy",
            6:"gray",
            7:"green",
            8:"navy blue",
            9:"of many colors",
            10:"olive",
            11:"pink",
            12:"red",
            13:"violet",
            14:"white"
        }
        # Replace colour
        cluster_summ.colour = cluster_summ.colour.replace(color_mapping)
        
        loc_mapping = {
            1:"top left",
            2:"top in the middle",
            3:"top right",
            4:"bottom left",
            5:"bottom in the middle",
            6:"bottom right"
        }
        # Replace location
        cluster_summ.location = cluster_summ.location.replace(loc_mapping)
        
        model_phot = {
            1:"en face",
            2:"profile"
        }
        # Replace Model Photography
        cluster_summ.model_photography = cluster_summ.model_photography.replace(model_phot)
        
        purch = {1:'Yes',2:'No'}
        # Replace Price 2
        cluster_summ.price_2 = cluster_summ.price_2.replace(purch)
        
        cluster_summ['order'] = np.expm1(cluster_summ['order_log'])
        cluster_summ.drop('order_log',axis=1,inplace=True)
        cluster_summ['date'] = pd.to_datetime(dict(year=2008,month=cluster_summ.month,day=cluster_summ.day))
        cluster_summ.drop(['month','day'],axis=1,inplace=True)
        categ = cluster_summ.select_dtypes(include=['object','datetime'])
        numeric = cluster_summ.select_dtypes(include='number')
        numeric.drop('Cluster_groups',axis=1,inplace=True)
        cluster_numerical_summ = cluster_summ.groupby('Cluster_groups').agg(price=('price','mean'),
                                                                         order=('order','median'),
                                                                         page=('page','median'))
        cluster_categorical_summ = cluster_summ.groupby('Cluster_groups')[categ.columns.to_list()].agg(lambda x: x.mode().iloc[0])
        cluster_numerical_summ[['order','page']] = np.ceil(cluster_numerical_summ[['order','page']])
        final_summ_stat = pd.concat([cluster_numerical_summ,cluster_categorical_summ],axis=1)
        st.write(":blue[**CLUSTERING RESULTS**]")
        st.dataframe(final_summ_stat)
        
        fig,ax = plt.subplots(2,2,figsize=(12,12))
        cluster_counts = cluster_click_unk['Cluster_groups'].value_counts().sort_index()

        # Plot
        bars = ax[0,0].bar(cluster_counts.index, cluster_counts.values, color='blue')

        # Add text **on top** of bars
        for bar in bars:
            height = bar.get_height()
            ax[0,0].text(bar.get_x() + bar.get_width() / 2, height + 100, 
                     f'{int(height)}', ha='center', va='bottom', fontsize=8)

        ax[0,0].set_title('Distribution of Cluster Group')
        ax[0,0].set_xlabel('Cluster Group')
        ax[0,0].set_ylabel('Frequency')
        ax[0,0].grid(False)
        
        cluster_mean = cluster_click_unk.groupby(['Cluster_groups']).agg(avg_price=('price','mean'))

        # Plot
        bars = ax[0,1].bar(cluster_mean.index.to_list(), cluster_mean.values.reshape(1,-1).tolist()[0], color='red')

        # Add text **on top** of bars
        for bar in bars:
            height = bar.get_height()
            ax[0,1].text(bar.get_x() + bar.get_width() / 2, height + 0.5, 
                     f'{height:.2f}', ha='center', va='bottom', fontsize=8)

        ax[0,1].set_title('Average Price for each Cluster group')
        ax[0,1].set_xlabel('Cluster Group')
        ax[0,1].set_ylabel('Average Price (in USD)')
        ax[0,1].grid(False) 
        
        fig.delaxes(ax[1,0])
        fig.delaxes(ax[1,1])
        st.pyplot(fig)
        
        # Proportion of customers who will purchase or not for each cluster group
        prop_df = cluster_summ.groupby('Cluster_groups')['price_2'].value_counts(normalize=True).unstack()
        
        fig, ax = plt.subplots(figsize=(6, 4))
        prop_df.plot(kind='bar',stacked=True,colormap='viridis',ax=ax)
        ax.set_title('Proportion of Purchase Decisions by Cluster Group')
        ax.set_xlabel('Cluster Group')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        ax.set_ylabel('Proportion')
        ax.legend(loc='center left',bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        st.pyplot(fig)
           

        
    