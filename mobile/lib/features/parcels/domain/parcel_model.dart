// lib/features/parcels/domain/parcel_model.dart
// ═══════════════════════════════════════════════════════════════

class ParcelModel {
  final String  id;
  final String  titre;
  final String  localisation;
  final String  region;
  final double  superficie;
  final double  prix;
  final String  typeTerrain;
  final String  statut;
  final String  vendeurNom;
  final String? photoPrincipale;
  final DateTime dateAjout;

  const ParcelModel({
    required this.id,
    required this.titre,
    required this.localisation,
    required this.region,
    required this.superficie,
    required this.prix,
    required this.typeTerrain,
    required this.statut,
    required this.vendeurNom,
    required this.dateAjout,
    this.photoPrincipale,
  });

  bool get isCertified => statut == 'certified' || statut == 'certifiee';

  factory ParcelModel.fromJson(Map<String, dynamic> j) => ParcelModel(
    id:               j['id']              as String,
    titre:            j['titre']           as String,
    localisation:     (j['localisation'] ?? j['region']) as String,
    region:           j['region']          as String,
    superficie:       (j['superficie']     as num).toDouble(),
    prix:             ((j['prix'] ?? j['price']) as num).toDouble(),
    typeTerrain:      j['type_terrain']    as String,
    statut:           (j['statut'] ?? j['status']) as String,
    vendeurNom:       j['vendeur_nom']     as String? ?? '',
    photoPrincipale:  j['photo_principale'] as String?,
    dateAjout:        DateTime.tryParse(j['date_ajout'] ?? '') ?? DateTime.now(),
  );

  String get prixFormate {
    if (prix >= 1000000000) return '${(prix / 1000000000).toStringAsFixed(1)}Md FCFA';
    if (prix >= 1000000)    return '${(prix / 1000000).toStringAsFixed(0)}M FCFA';
    return '${prix.toStringAsFixed(0)} FCFA';
  }
}

class ParcelsResponse {
  final int count;
  final List<ParcelModel> results;
  ParcelsResponse({required this.count, required this.results});

  factory ParcelsResponse.fromJson(Map<String, dynamic> j) => ParcelsResponse(
    count:   j['count'] as int,
    results: (j['results'] as List).map((e) => ParcelModel.fromJson(e)).toList(),
  );
}

class ParcelDetail extends ParcelModel {
  final String?              description;
  final double?              latitude;
  final double?              longitude;
  final String?              documentHash;
  final String?              blockchainTxHash;
  final CertificatInfo?      certificat;

  const ParcelDetail({
    required super.id,       required super.titre,
    required super.localisation, required super.region,
    required super.superficie, required super.prix,
    required super.typeTerrain, required super.statut,
    required super.vendeurNom, required super.dateAjout,
    super.photoPrincipale,
    this.description,        this.latitude,
    this.longitude,          this.documentHash,
    this.blockchainTxHash,   this.certificat,
  });

  factory ParcelDetail.fromJson(Map<String, dynamic> j) => ParcelDetail(
    id:               j['id']           as String,
    titre:            j['titre']        as String,
    localisation:     (j['localisation'] ?? j['region']) as String,
    region:           j['region']       as String,
    superficie:       (j['superficie']  as num).toDouble(),
    prix:             ((j['prix'] ?? j['price']) as num).toDouble(),
    typeTerrain:      j['type_terrain'] as String,
    statut:           (j['statut'] ?? j['status']) as String,
    vendeurNom:       j['vendeur_nom']  as String? ?? '',
    dateAjout:        DateTime.tryParse(j['date_ajout'] ?? '') ?? DateTime.now(),
    photoPrincipale:  j['photo_principale'] as String?,
    description:      j['description'] as String?,
    latitude:         (j['location']?['latitude'] as num?)?.toDouble(),
    longitude:        (j['location']?['longitude'] as num?)?.toDouble(),
    documentHash:     j['document_hash'] as String?,
    blockchainTxHash: j['blockchain_tx_hash'] as String?,
    certificat: j['certificat'] != null
        ? CertificatInfo.fromJson(j['certificat']) : null,
  );
}

class CertificatInfo {
  final String hashBlockchain;
  final DateTime dateValidation;
  CertificatInfo({required this.hashBlockchain, required this.dateValidation});
  factory CertificatInfo.fromJson(Map<String, dynamic> j) => CertificatInfo(
    hashBlockchain: j['hash_blockchain'] as String,
    dateValidation: DateTime.parse(j['date_validation'] as String),
  );
}


// ═══════════════════════════════════════════════════════════════