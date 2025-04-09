import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
import glob

# Configuration de la page avec un thème plus élégant
st.set_page_config(
    page_title="Tracker de Dépenses",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Charger le fichier CSS externe
def load_css(css_file):
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Charger le fichier CSS
load_css("style.css")

# Initialisation des variables de session
if 'receipts' not in st.session_state:
    st.session_state.receipts = []
if 'monthly_totals' not in st.session_state:
    st.session_state.monthly_totals = {}

# Fonction pour créer les dossiers nécessaires
def create_folder_structure():
    os.makedirs("data", exist_ok=True)
    os.makedirs("receipts", exist_ok=True)

# Fonction pour générer un nom de fichier unique
def generate_unique_filename(date, enterprise):
    base_filename = f"{date}_{enterprise.replace(' ', '_')}.md"
    year_month = date.split('-')[0] + '_' + date.split('-')[1]
    folder_path = os.path.join("receipts", year_month)
    os.makedirs(folder_path, exist_ok=True)
    
    counter = 1
    filename = base_filename
    while os.path.exists(os.path.join(folder_path, filename)):
        filename = f"{date}_{enterprise.replace(' ', '_')}_{counter}.md"
        counter += 1
    
    return year_month, filename

# Fonction pour sauvegarder un ticket en markdown
def save_receipt_as_markdown(date, enterprise, total, category, notes):
    year_month, filename = generate_unique_filename(date, enterprise)
    filepath = os.path.join("receipts", year_month, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# Ticket: {enterprise}\n\n")
        f.write(f"**Date:** {date}\n\n")
        f.write(f"**Catégorie:** {category}\n\n")
        f.write(f"**Total:** {total}€\n\n")
        f.write("## Notes\n\n")
        f.write(notes if notes else "_Aucune note_")
    
    # Mise à jour des données de session
    update_session_data()
    
    return year_month, filename

# Fonction pour charger tous les tickets
def load_all_receipts():
    receipts = []
    receipt_folders = glob.glob("receipts/*_*/")
    
    for folder in receipt_folders:
        receipt_files = glob.glob(os.path.join(folder, "*.md"))
        for receipt_file in receipt_files:
            year_month = os.path.basename(os.path.dirname(receipt_file))
            filename = os.path.basename(receipt_file)
            
            # Extraire les informations du nom de fichier
            date_match = re.match(r"(\d{4}-\d{2}-\d{2})_(.+?)(?:_\d+)?\.md$", filename)
            if date_match:
                date = date_match.group(1)
                enterprise = date_match.group(2).replace('_', ' ')
                
                # Lire le contenu pour extraire le total et la catégorie
                try:
                    with open(receipt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        total_match = re.search(r'\*\*Total:\*\* (\d+(?:\.\d+)?)€', content)
                        category_match = re.search(r'\*\*Catégorie:\*\* (.+?)\n', content)
                        
                        category = category_match.group(1) if category_match else "Non catégorisé"
                        total = float(total_match.group(1)) if total_match else 0.0
                        
                        receipts.append({
                            'date': date,
                            'enterprise': enterprise,
                            'total': total,
                            'category': category,
                            'year_month': year_month,
                            'filename': filename
                        })
                except Exception as e:
                    st.warning(f"Erreur lors de la lecture de {receipt_file}: {str(e)}")
    
    # Trier par date (plus récent au plus ancien)
    receipts.sort(key=lambda x: x['date'], reverse=True)
    return receipts

# Fonction pour supprimer un ticket
def delete_receipt(year_month, filename):
    filepath = os.path.join("receipts", year_month, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        # Vérifier si le dossier est vide après suppression
        if not os.listdir(os.path.join("receipts", year_month)):
            os.rmdir(os.path.join("receipts", year_month))
        update_session_data()
        return True
    return False

# Fonction pour afficher un ticket
def view_receipt(year_month, filename):
    filepath = os.path.join("receipts", year_month, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    return None

# Fonction pour calculer les totaux mensuels
def calculate_monthly_totals(receipts):
    monthly_totals = {}
    for receipt in receipts:
        year_month = receipt['year_month']
        if year_month in monthly_totals:
            monthly_totals[year_month] += receipt['total']
        else:
            monthly_totals[year_month] = receipt['total']
    
    # Trier par date
    sorted_totals = {k: monthly_totals[k] for k in sorted(monthly_totals.keys(), reverse=True)}
    return sorted_totals

# Fonction pour calculer les totaux par catégorie
def calculate_category_totals(receipts):
    category_totals = {}
    for receipt in receipts:
        category = receipt['category']
        if category in category_totals:
            category_totals[category] += receipt['total']
        else:
            category_totals[category] = receipt['total']
    
    # Trier par montant (du plus grand au plus petit)
    sorted_totals = {k: v for k, v in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)}
    return sorted_totals

# Fonction pour mettre à jour les données de session
def update_session_data():
    st.session_state.receipts = load_all_receipts()
    st.session_state.monthly_totals = calculate_monthly_totals(st.session_state.receipts)

# Interface utilisateur
def main():
    create_folder_structure()
    
    # Titre élégant
    st.markdown("<h1 class='main-header'>Tracker de Dépenses</h1>", unsafe_allow_html=True)
    
    # Si c'est le premier chargement, charger tous les tickets
    if not st.session_state.receipts:
        update_session_data()
    
    # Disposition en deux colonnes
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("<div class='card'><h2 class='sub-header'>Saisie de Ticket</h2>", unsafe_allow_html=True)
        
        # Formulaire d'ajout manuel amélioré
        with st.form("manual_form"):
            cols_form1 = st.columns(2)
            with cols_form1[0]:
                manual_date = st.date_input("Date", value=datetime.now())
            with cols_form1[1]:
                manual_enterprise = st.text_input("Entreprise")
            
            cols_form2 = st.columns(2)
            with cols_form2[0]:
                manual_total = st.number_input("Montant total (€)", value=0.0, format="%.2f", min_value=0.0)
            with cols_form2[1]:
                # Liste des catégories prédéfinies mais modifiables
                categories = ["Alimentation", "Transport", "Logement", "Loisirs", "Santé", "Vêtements", "Restaurant", "Autre"]
                manual_category = st.selectbox("Catégorie", categories)
            
            manual_notes = st.text_area("Notes (optionnel)")
            
            manual_submitted = st.form_submit_button("Enregistrer le ticket")
            
            if manual_submitted and manual_enterprise and manual_total > 0:
                date_str = manual_date.strftime('%Y-%m-%d')
                year_month, filename = save_receipt_as_markdown(date_str, manual_enterprise, manual_total, manual_category, manual_notes)
                st.success(f"✅ Ticket '{manual_enterprise}' sauvegardé avec succès!")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Liste des tickets
        st.markdown("<div class='card'><h2 class='sub-header'>Liste des Tickets</h2>", unsafe_allow_html=True)
        
        if not st.session_state.receipts:
            st.info("📝 Aucun ticket enregistré.")
        else:
            # Filtres
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                # Extraire les mois uniques
                unique_months = list(set([r['year_month'] for r in st.session_state.receipts]))
                unique_months.sort(reverse=True)
                month_labels = ["Tous les mois"] + [f"{m.split('_')[0]}-{m.split('_')[1]}" for m in unique_months]
                month_values = ["all"] + unique_months
                selected_month = st.selectbox("Filtrer par mois", options=month_values, format_func=lambda x: month_labels[month_values.index(x)])
            
            with col_filter2:
                # Extraire les catégories uniques
                unique_categories = list(set([r['category'] for r in st.session_state.receipts]))
                unique_categories.sort()
                category_options = ["Toutes les catégories"] + unique_categories
                selected_category = st.selectbox("Filtrer par catégorie", options=category_options)
            
            # Filtrer les tickets
            filtered_receipts = st.session_state.receipts
            if selected_month != "all":
                filtered_receipts = [r for r in filtered_receipts if r['year_month'] == selected_month]
            
            if selected_category != "Toutes les catégories":
                filtered_receipts = [r for r in filtered_receipts if r['category'] == selected_category]
            
            # Afficher le nombre de tickets filtrés
            st.write(f"🧾 {len(filtered_receipts)} ticket(s) trouvé(s)")
            
            # Grouper par mois
            months = {}
            for receipt in filtered_receipts:
                if receipt['year_month'] not in months:
                    months[receipt['year_month']] = []
                months[receipt['year_month']].append(receipt)
            
            # Afficher par mois
            sorted_months = sorted(months.items(), reverse=True)
            for i, (month, receipts) in enumerate(sorted_months):
                year, month_num = month.split('_')
                month_name = datetime(int(year), int(month_num), 1).strftime('%B %Y').capitalize()
                monthly_total = sum(r['total'] for r in receipts)
                
                # On garde le premier mois déroulé, les autres seront fermés par défaut
                is_expanded = (i == 0)
                
                with st.expander(f"📅 {month_name} - Total: {monthly_total:.2f}€", expanded=is_expanded):
                    for receipt in receipts:
                        # Format simple pour les tickets
                        st.markdown(f"""
                        <div class='ticket-text'>
                            <strong>{receipt['date']}</strong> | {receipt['enterprise']} | 
                            <span style='color:#1E88E5'>{receipt['total']:.2f}€</span> | 
                            <span style='background-color:#e3f2fd; padding:2px 8px; border-radius:12px; font-size:0.8em'>{receipt['category']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_btn1, _ ,col_btn2, _= st.columns([2, 1, 2, 6])
                        with col_btn1:
                            if st.button("🔍 Détails", key=f"view_{receipt['year_month']}_{receipt['filename']}"):
                                content = view_receipt(receipt['year_month'], receipt['filename'])
                                if content:
                                    st.session_state.viewing_receipt = content
                                    st.session_state.viewing_title = f"{receipt['date']} - {receipt['enterprise']}"
                        
                        with col_btn2:
                            if st.button("🗑️ Supprimer", key=f"delete_{receipt['year_month']}_{receipt['filename']}"):
                                if delete_receipt(receipt['year_month'], receipt['filename']):
                                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'><h2 class='sub-header'>Statistiques & Graphiques</h2>", unsafe_allow_html=True)
        
        # Afficher graphique des dépenses mensuelles avec un design amélioré
        if st.session_state.monthly_totals:
            # Préparation des données
            months = list(st.session_state.monthly_totals.keys())
            totals = list(st.session_state.monthly_totals.values())
            
            # Convertir les clés année_mois en dates lisibles
            readable_months = []
            for m in months:
                year, month = m.split('_')
                month_name = datetime(int(year), int(month), 1).strftime('%b %y')
                readable_months.append(month_name)
            
            # Créer le dataframe
            df = pd.DataFrame({
                'Mois': readable_months,
                'Total': totals,
                'Mois_Sort': [datetime.strptime(f"{m.split('_')[0]}-{m.split('_')[1]}", '%Y-%m') for m in months]
            })
            
            # Trier par date
            df = df.sort_values(by='Mois_Sort')
            
            # Onglets pour différents graphiques
            tab1, tab2 = st.tabs(["📊 Évolution Mensuelle", "🔄 Répartition par Catégorie"])
            
            with tab1:
                # Créer le graphique des dépenses mensuelles
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Palette de couleurs élégante
                bars = ax.bar(df['Mois'], df['Total'], color=sns.color_palette("viridis", len(df)))
                
                ax.set_title('Évolution des Dépenses Mensuelles', fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Mois', fontsize=12)
                ax.set_ylabel('Montant (€)', fontsize=12)
                
                # Améliorer l'apparence
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#DDDDDD')
                ax.spines['bottom'].set_color('#DDDDDD')
                ax.tick_params(bottom=False, left=False)
                
                # Ajouter une grille légère
                ax.yaxis.grid(True, color='#EEEEEE')
                ax.xaxis.grid(False)
                
                # Rotation des labels
                plt.xticks(rotation=45, ha='right')
                
                # Ajouter les valeurs sur les barres
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(totals)*0.02,
                           f"{height:.2f}€",
                           ha='center', va='bottom', fontweight='bold', color='#1E88E5')
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Statistiques en cartes élégantes
                st.markdown("<h3 style='text-align:center; margin:20px 0;'>Vue d'ensemble</h3>", unsafe_allow_html=True)
                
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                
                with stats_col1:
                    total_depense = sum(totals)
                    st.markdown(f"""
                    <div style='text-align:center; padding:20px; background-color:white; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);'>
                        <div class='metric-label'>Total des dépenses</div>
                        <div class='metric-value'>{total_depense:.2f}€</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with stats_col2:
                    avg_mensuel = sum(totals)/len(totals) if totals else 0
                    st.markdown(f"""
                    <div style='text-align:center; padding:20px; background-color:white; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);'>
                        <div class='metric-label'>Moyenne mensuelle</div>
                        <div class='metric-value'>{avg_mensuel:.2f}€</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with stats_col3:
                    max_mensuel = max(totals) if totals else 0
                    max_month = readable_months[totals.index(max_mensuel)] if totals else ""
                    st.markdown(f"""
                    <div style='text-align:center; padding:20px; background-color:white; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);'>
                        <div class='metric-label'>Mois le plus coûteux</div>
                        <div class='metric-value'>{max_mensuel:.2f}€</div>
                        <div style='font-size:14px; color:#757575;'>{max_month}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Tendance des 3 derniers mois
                if len(totals) >= 3:
                    last_3_months = totals[:3]  # Les données sont déjà triées du plus récent au plus ancien
                    last_3_months_avg = sum(last_3_months) / 3
                    overall_avg = avg_mensuel
                    
                    trend_percentage = ((last_3_months_avg - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
                    
                    trend_color = "#EF5350" if trend_percentage > 0 else "#66BB6A"
                    trend_icon = "↑" if trend_percentage > 0 else "↓"
                    
                    st.markdown(f"""
                    <div style='text-align:center; margin-top:20px; padding:15px; background-color:white; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);'>
                        <div class='metric-label'>Tendance sur les 3 derniers mois</div>
                        <div style='font-size:24px; font-weight:600; color:{trend_color};'>
                            {trend_icon} {abs(trend_percentage):.1f}% par rapport à la moyenne
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with tab2:
                # Calculer les totaux par catégorie
                category_totals = calculate_category_totals(st.session_state.receipts)
                
                if category_totals:
                    # Créer le dataframe
                    df_cat = pd.DataFrame({
                        'Catégorie': list(category_totals.keys()),
                        'Total': list(category_totals.values())
                    })
                    
                    # Créer le graphique en camembert
                    fig, ax = plt.subplots(figsize=(10, 7))
                    
                    # Utiliser une belle palette de couleurs
                    colors = sns.color_palette('viridis', len(df_cat))
                    
                    wedges, texts, autotexts = ax.pie(
                        df_cat['Total'], 
                        labels=list(df_cat['Catégorie']), #None,
                        autopct='',
                        startangle=90,
                        colors=colors,
                        wedgeprops=dict(width=0.5, edgecolor='w')
                    )
                    
                    # Calculer le pourcentage pour chaque catégorie
                    total_amount = sum(df_cat['Total'])
                    percentages = [(amount/total_amount)*100 for amount in df_cat['Total']]
                    
                    # Ajouter une légende élégante
                    legend_labels = [f"{cat} ({per:.1f}% - {amount:.2f}€)" for cat, per, amount in zip(df_cat['Catégorie'], percentages, df_cat['Total'])]
                    ax.legend(wedges, legend_labels, title="Catégories", loc="best", bbox_to_anchor=(1, 0, 0.5, 1))
                    
                    plt.title('Répartition des Dépenses par Catégorie', fontsize=16, fontweight='bold', pad=20)
                    ax.set_aspect('equal')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Top 3 des catégories les plus coûteuses
                    st.markdown("<h3 style='text-align:center; margin:20px 0;'>Top 3 des catégories</h3>", unsafe_allow_html=True)
                    
                    top_cats = list(category_totals.items())[:3]  # Déjà trié du plus grand au plus petit
                    
                    cat_cols = st.columns(3)
                    for i, (cat, amount) in enumerate(top_cats):
                        if i < len(cat_cols):
                            with cat_cols[i]:
                                percent = (amount / total_amount) * 100
                                st.markdown(f"""
                                <div style='text-align:center; padding:15px; background-color:white; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05);'>
                                    <div style='font-size:14px; color:#757575;'>{i+1}. {cat}</div>
                                    <div class='metric-value'>{amount:.2f}€</div>
                                    <div style='font-size:14px; color:#1E88E5;'>{percent:.1f}% du total</div>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.info("Aucune donnée de catégorie disponible pour afficher le graphique.")
        else:
            st.info("Aucune donnée disponible pour afficher les graphiques.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Afficher le contenu d'un ticket si demandé
        if 'viewing_receipt' in st.session_state:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<h2 class='sub-header'>Détail du Ticket: {st.session_state.viewing_title}</h2>", unsafe_allow_html=True)
            
            # Wrapper pour le contenu du ticket avec une ombre plus prononcée
            st.markdown("<div class='ticket-detail-card'>", unsafe_allow_html=True)
            st.markdown(st.session_state.viewing_receipt)
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("Fermer"):
                del st.session_state.viewing_receipt
                del st.session_state.viewing_title
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()