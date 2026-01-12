if st.button("Générer la carte"):
    if not card_code or not card_code.isdigit():
        st.error("Veuillez entrer uniquement des chiffres")
    else:
        # Génération code-barres Code128
        code128 = Code128(card_code, writer=ImageWriter())
        code128.save("code128_card", options={
            "write_text": True,
            "add_checksum": False,
            "background": "white",
            "foreground": "black",
            "module_width": 0.35,   # légèrement plus large pour voir tous les chiffres
            "module_height": 120,   # ~4cm, pour que les chiffres + barre soient visibles
            "font_size": 18          # texte lisible
        })

        barcode_img = Image.open("code128_card.png")

        st.subheader("Aperçu de la carte fidélité")
        st.image(barcode_img)

        # Télécharger pour impression
        output_buffer = BytesIO()
        barcode_img.save(output_buffer, format="PNG")
        st.download_button(
            label="📥 Télécharger la carte pour impression",
            data=output_buffer.getvalue(),
            file_name="carte_fidelite.png",
            mime="image/png"
        )
