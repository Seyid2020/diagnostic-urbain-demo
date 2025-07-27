valid_indicators += 1
        
        if values:
            # Normalisation des scores (0-100)
            avg_value = np.mean(values)
            # Score basé sur la moyenne normalisée (ajustement selon le contexte)
            if category in ["Société", "Logement", "Infrastructure"]:
                # Pour ces dimensions, plus c'est élevé, mieux c'est
                score = min(100, avg_value)
            elif category == "Environnement":
                # Pour l'environnement, certains indicateurs sont inversés (pollution)
                score = max(0, 100 - avg_value) if avg_value > 50 else avg_value
            else:
                score = min(100, avg_value)
            
            dimension_scores[category] = score
        else:
            dimension_scores[category] = 0
        
        dimension_details[category] = {
            'score': dimension_scores[category],
            'valid_indicators': valid_indicators,
            'total_indicators': total_indicators,
            'completion_rate': (valid_indicators / total_indicators) * 100
        }
    
    # Métriques principales
    st.subheader("🎯 Métriques Clés")
    
    cols = st.columns(len(dimension_scores))
    for i, (category, score) in enumerate(dimension_scores.items()):
        with cols[i]:
            # Couleur basée sur le score
            if score >= 70:
                color = "#28a745"
                status = "Excellent"
            elif score >= 50:
                color = "#ffc107"
                status = "Satisfaisant"
            else:
                color = "#dc3545"
                status = "À améliorer"
            
            st.markdown(f"""
            <div style="background: {color}; color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-size: 0.9rem;">{category}</h4>
                <h2 style="margin: 0.5rem 0; font-size: 2rem;">{score:.1f}</h2>
                <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">{status}</p>
                <p style="margin: 0; font-size: 0.7rem; opacity: 0.8;">{dimension_details[category]['valid_indicators']}/{dimension_details[category]['total_indicators']} indicateurs</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Graphiques principaux
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕸️ Profil Urbain - Radar")
        
        # Graphique radar
        categories = list(dimension_scores.keys())
        values = list(dimension_scores.values())
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=city_data['city'],
            line=dict(color='#2a5298', width=3),
            fillcolor='rgba(42, 82, 152, 0.3)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10),
                    gridcolor='rgba(0,0,0,0.1)'
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color='#495057')
                )
            ),
            showlegend=False,
            title=dict(
                text=f"Profil de {city_data['city']}",
                x=0.5,
                font=dict(size=16, color='#2a5298')
            ),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        st.subheader("📊 Scores par Dimension")
        
        # Graphique en barres
        fig_bar = px.bar(
            x=list(dimension_scores.values()),
            y=list(dimension_scores.keys()),
            orientation='h',
            color=list(dimension_scores.values()),
            color_continuous_scale=['#dc3545', '#ffc107', '#28a745'],
            range_color=[0, 100]
        )
        
        fig_bar.update_layout(
            title=dict(
                text="Performance par Dimension",
                font=dict(size=16, color='#2a5298')
            ),
            xaxis_title="Score (0-100)",
            yaxis_title="",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        fig_bar.update_traces(
            texttemplate='%{x:.1f}',
            textposition='inside',
            textfont=dict(color='white', size=12)
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Analyse détaillée par dimension
    st.subheader("🔍 Analyse Détaillée par Dimension")
    
    # Sélecteur de dimension
    selected_dimension = st.selectbox(
        "Choisir une dimension à analyser",
        list(indicators_data.keys()),
        help="Sélectionnez une dimension pour voir le détail des indicateurs"
    )
    
    if selected_dimension:
        dimension_data = indicators_data[selected_dimension]
        
        # Statistiques de la dimension
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Score Global",
                f"{dimension_scores[selected_dimension]:.1f}/100",
                help="Score moyen de la dimension"
            )
        
        with col2:
            completion = dimension_details[selected_dimension]['completion_rate']
            st.metric(
                "Complétude",
                f"{completion:.1f}%",
                help="Pourcentage d'indicateurs avec des données"
            )
        
        with col3:
            valid_count = dimension_details[selected_dimension]['valid_indicators']
            st.metric(
                "Indicateurs Valides",
                f"{valid_count}",
                help="Nombre d'indicateurs avec des données"
            )
        
        with col4:
            total_count = dimension_details[selected_dimension]['total_indicators']
            st.metric(
                "Total Indicateurs",
                f"{total_count}",
                help="Nombre total d'indicateurs dans cette dimension"
            )
        
        # Tableau détaillé des indicateurs
        st.markdown("### 📋 Détail des Indicateurs")
        
        # Préparation des données pour le tableau
        table_data = []
        for code, data in dimension_data.items():
            value = data['value'] if not pd.isna(data['value']) else 'N/A'
            if isinstance(value, (int, float)) and not pd.isna(value):
                if abs(value) >= 1000:
                    value_str = f"{value:,.1f}"
                else:
                    value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            
            # Statut basé sur la disponibilité des données
            status = "✅ Disponible" if not pd.isna(data['value']) else "❌ Manquant"
            
            table_data.append({
                'Indicateur': data['name'],
                'Valeur': value_str,
                'Unité': data['unit'],
                'Année': data['year'] if data['year'] else 'N/A',
                'Source': data['source'][:40] + '...' if len(data['source']) > 40 else data['source'],
                'Statut': status,
                'Commentaire': data.get('comment', '') or 'Aucun'
            })
        
        # Affichage du tableau avec filtres
        df_table = pd.DataFrame(table_data)
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filtrer par statut",
                ["✅ Disponible", "❌ Manquant"],
                default=["✅ Disponible", "❌ Manquant"]
            )
        
        with col2:
            search_term = st.text_input(
                "Rechercher un indicateur",
                placeholder="Tapez pour filtrer..."
            )
        
        # Application des filtres
        filtered_df = df_table[df_table['Statut'].isin(status_filter)]
        if search_term:
            filtered_df = filtered_df[
                filtered_df['Indicateur'].str.contains(search_term, case=False, na=False)
            ]
        
        # Affichage du tableau filtré
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Indicateur': st.column_config.TextColumn('Indicateur', width='large'),
                'Valeur': st.column_config.TextColumn('Valeur', width='small'),
                'Unité': st.column_config.TextColumn('Unité', width='small'),
                'Année': st.column_config.TextColumn('Année', width='small'),
                'Source': st.column_config.TextColumn('Source', width='medium'),
                'Statut': st.column_config.TextColumn('Statut', width='small'),
                'Commentaire': st.column_config.TextColumn('Commentaire', width='medium')
            }
        )
    
    # Graphiques comparatifs
    st.subheader("📈 Analyses Comparatives")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique de complétude des données
        completion_data = {
            'Dimension': list(dimension_details.keys()),
            'Taux de Complétude (%)': [details['completion_rate'] for details in dimension_details.values()]
        }
        
        fig_completion = px.bar(
            completion_data,
            x='Taux de Complétude (%)',
            y='Dimension',
            orientation='h',
            title="Complétude des Données par Dimension",
            color='Taux de Complétude (%)',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        
        fig_completion.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        
        fig_completion.update_traces(
            texttemplate='%{x:.1f}%',
            textposition='inside'
        )
        
        st.plotly_chart(fig_completion, use_container_width=True)
    
    with col2:
        # Graphique de distribution des scores
        fig_dist = px.pie(
            values=list(dimension_scores.values()),
            names=list(dimension_scores.keys()),
            title="Distribution des Scores par Dimension",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig_dist.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=10
        )
        
        fig_dist.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # Recommandations basées sur les données
    st.subheader("💡 Recommandations Intelligentes")
    
    # Analyse automatique des points faibles
    weak_dimensions = [dim for dim, score in dimension_scores.items() if score < 50]
    strong_dimensions = [dim for dim, score in dimension_scores.items() if score >= 70]
    
    col1, col2 = st.columns(2)
    
    with col1:
        if weak_dimensions:
            st.markdown("#### 🔴 Dimensions Prioritaires")
            for dim in weak_dimensions:
                score = dimension_scores[dim]
                st.markdown(f"""
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 1rem; margin-bottom: 0.5rem; border-radius: 5px;">
                    <strong>{dim}</strong> (Score: {score:.1f}/100)<br>
                    <small>Nécessite une attention immédiate et des investissements prioritaires</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Aucune dimension critique identifiée")
    
    with col2:
        if strong_dimensions:
            st.markdown("#### 🟢 Points Forts")
            for dim in strong_dimensions:
                score = dimension_scores[dim]
                st.markdown(f"""
                <div style="background: #d1edff; border-left: 4px solid #28a745; padding: 1rem; margin-bottom: 0.5rem; border-radius: 5px;">
                    <strong>{dim}</strong> (Score: {score:.1f}/100)<br>
                    <small>Performance satisfaisante, maintenir les efforts</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Aucun point fort majeur identifié")
    
    # Export des données
    st.subheader("📤 Export des Données")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export CSV des indicateurs
        all_indicators_data = []
        for category, indicators in indicators_data.items():
            for code, data in indicators.items():
                all_indicators_data.append({
                    'Dimension': category,
                    'Code': code,
                    'Indicateur': data['name'],
                    'Valeur': data['value'],
                    'Unité': data['unit'],
                    'Année': data['year'],
                    'Source': data['source'],
                    'Commentaire': data.get('comment', '')
                })
        
        df_export = pd.DataFrame(all_indicators_data)
        csv_data = df_export.to_csv(index=False)
        
        st.download_button(
            label="📊 Export CSV",
            data=csv_data,
            file_name=f"indicateurs_{city_data['city']}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export JSON des scores
        scores_data = {
            'ville': city_data,
            'scores_dimensions': dimension_scores,
            'details_dimensions': dimension_details,
            'date_export': datetime.now().isoformat()
        }
        
        json_data = json.dumps(scores_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            label="📋 Export JSON",
            data=json_data,
            file_name=f"scores_{city_data['city']}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        # Régénération du rapport PDF
        if st.button("🔄 Régénérer PDF", use_container_width=True):
            with st.spinner("Génération en cours..."):
                pdf_buffer = generate_advanced_pdf_report(
                    city_data, 
                    indicators_data, 
                    diagnostic_info,
                    data.get('documents', [])
                )
                
                st.download_button(
                    label="📥 Télécharger PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"diagnostic_urbain_{city_data['city']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

def chatbot_tab():
    """Interface de chatbot IA avancé"""
    
    st.markdown("### 🤖 Assistant IA Spécialisé en Diagnostic Urbain")
    
    # Initialisation de l'historique des conversations
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Informations sur les capacités du chatbot
    with st.expander("ℹ️ Capacités de l'Assistant IA"):
        st.markdown("""
        **🧠 Intelligence Hybride :**
        - **Analyse locale** : Traitement de vos données de diagnostic
        - **Recherche documentaire** : RAG sur vos documents uploadés
        - **Connaissances globales** : Meilleures pratiques internationales
        - **Recommandations** : Suggestions personnalisées basées sur vos données
        
        **💬 Types de questions supportées :**
        - Interprétation des indicateurs et scores
        - Comparaisons avec d'autres villes
        - Recommandations d'amélioration
        - Méthodologies de diagnostic urbain
        - Recherche dans vos documents
        """)
    
    # Zone de chat
    chat_container = st.container()
    
    # Affichage de l'historique des conversations
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 Vous :</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistant :</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
    
    # Interface de saisie
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Posez votre question :",
            placeholder="Ex: Comment interpréter le score de la dimension Logement ?",
            key="chat_input"
        )
    
    with col2:
        send_button = st.button("📤 Envoyer", type="primary", use_container_width=True)
    
    # Suggestions de questions
    st.markdown("**💡 Questions suggérées :**")
    
    suggestion_cols = st.columns(3)
    
    suggestions = [
        "Quels sont les points faibles de ma ville ?",
        "Comment améliorer le score de logement ?",
        "Comparez avec les standards internationaux",
        "Que disent mes documents sur l'urbanisme ?",
        "Quelles sont les priorités d'investissement ?",
        "Comment interpréter les indicateurs économiques ?"
    ]
    
    for i, suggestion in enumerate(suggestions):
        col_index = i % 3
        with suggestion_cols[col_index]:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                user_input = suggestion
                send_button = True
    
    # Traitement de la question
    if (send_button and user_input) or user_input:
        if user_input.strip():
            # Ajout de la question à l'historique
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Préparation du contexte
            context_data = {}
            documents = []
            
            # Récupération des données du diagnostic si disponibles
            if 'final_report_data' in st.session_state:
                context_data = st.session_state.final_report_data
                documents = context_data.get('documents', [])
            elif 'processed_documents' in st.session_state:
                documents = st.session_state.processed_documents
            
            # Génération de la réponse
            with st.spinner("🤔 Réflexion en cours..."):
                response = generate_advanced_ai_response(
                    user_input, 
                    context_data, 
                    documents
                )
            
            # Ajout de la réponse à l'historique
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            
            # Rerun pour afficher la nouvelle conversation
            st.rerun()
    
    # Options avancées
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Effacer l'historique", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.session_state.chat_history:
            # Export de la conversation
            chat_export = "\n\n".join([
                f"{'👤 UTILISATEUR' if msg['role'] == 'user' else '🤖 ASSISTANT'}: {msg['content']}"
                for msg in st.session_state.chat_history
            ])
            
            st.download_button(
                label="📥 Export Chat",
                data=chat_export,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col3:
        # Statistiques de la conversation
        if st.session_state.chat_history:
            total_messages = len(st.session_state.chat_history)
            user_messages = len([msg for msg in st.session_state.chat_history if msg['role'] == 'user'])
            
            st.metric(
                "Messages échangés",
                f"{total_messages}",
                f"{user_messages} questions"
            )

# Point d'entrée principal
if __name__ == "__main__":
    main()
