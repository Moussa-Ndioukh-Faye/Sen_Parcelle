import 'package:flutter_test/flutter_test.dart';
import 'package:sen_parcelle/features/parcels/domain/parcel_model.dart';

void main() {
  group('ParcelModel', () {
    test('devrait être créé depuis JSON avec champs français', () {
      final json = {
        'id': 'parcel-1',
        'titre': 'Terrain Test',
        'localisation': 'Dakar',
        'region': 'Dakar',
        'superficie': 500,
        'prix': 25000000,
        'type_terrain': 'residentiel',
        'statut': 'certifiee',
        'vendeur_nom': 'Moussa',
        'date_ajout': '2026-05-10T12:00:00Z',
        'photo_principale': 'http://example.com/photo.jpg',
      };

      final parcel = ParcelModel.fromJson(json);
      expect(parcel.id, 'parcel-1');
      expect(parcel.titre, 'Terrain Test');
      expect(parcel.superficie, 500);
      expect(parcel.prix, 25000000);
      expect(parcel.statut, 'certifiee');
      expect(parcel.vendeurNom, 'Moussa');
      expect(parcel.photoPrincipale, 'http://example.com/photo.jpg');
    });

    test('devrait gérer les champs anglais pour la rétrocompatibilité', () {
      final json = {
        'id': 'parcel-2',
        'titre': 'Terrain',
        'localisation': 'Thies',
        'region': 'Thies',
        'superficie': 300,
        'prix': 15000000,
        'type_terrain': 'agricole',
        'status': 'pending',
        'vendeur_nom': 'Ali',
        'date_ajout': '2026-01-01T00:00:00Z',
      };

      final parcel = ParcelModel.fromJson(json);
      expect(parcel.prix, 15000000);
      expect(parcel.statut, 'pending');
    });

    test('prixFormate devrait formater en FCFA', () {
      final json = {
        'id': 'p1',
        'titre': 'Test',
        'localisation': 'Dakar',
        'region': 'Dakar',
        'superficie': 100,
        'prix': 25000000,
        'type_terrain': 'residentiel',
        'statut': 'pending',
        'vendeur_nom': 'Test',
        'date_ajout': '2026-01-01T00:00:00Z',
      };
      final parcel = ParcelModel.fromJson(json);
      expect(parcel.prixFormate, contains('25'));
    });

    test('isCertified devrait être vrai pour certifiee', () {
      final json = {
        'id': 'p1',
        'titre': 'Test',
        'localisation': 'Dakar',
        'region': 'Dakar',
        'superficie': 100,
        'prix': 5000000,
        'type_terrain': 'residentiel',
        'statut': 'certifiee',
        'vendeur_nom': 'T',
        'date_ajout': '2026-01-01T00:00:00Z',
      };
      final parcel = ParcelModel.fromJson(json);
      expect(parcel.isCertified, true);
    });

    test('isCertified devrait être vrai pour certified', () {
      final json = {
        'id': 'p1',
        'titre': 'Test',
        'localisation': 'Dakar',
        'region': 'Dakar',
        'superficie': 100,
        'prix': 5000000,
        'type_terrain': 'residentiel',
        'statut': 'certified',
        'vendeur_nom': 'T',
        'date_ajout': '2026-01-01T00:00:00Z',
      };
      final parcel = ParcelModel.fromJson(json);
      expect(parcel.isCertified, true);
    });

    test('isCertified devrait être faux pour pending', () {
      final json = {
        'id': 'p1',
        'titre': 'Test',
        'localisation': 'Dakar',
        'region': 'Dakar',
        'superficie': 100,
        'prix': 5000000,
        'type_terrain': 'residentiel',
        'statut': 'pending',
        'vendeur_nom': 'T',
        'date_ajout': '2026-01-01T00:00:00Z',
      };
      final parcel = ParcelModel.fromJson(json);
      expect(parcel.isCertified, false);
    });
  });

  group('ParcelDetail', () {
    test('devrait être créé depuis JSON', () {
      final json = {
        'id': 'parcel-1',
        'titre': 'Terrain Test',
        'localisation': 'Dakar',
        'region': 'Dakar',
        'superficie': 500,
        'prix': 25000000,
        'type_terrain': 'residentiel',
        'statut': 'certifiee',
        'vendeur_nom': 'Moussa',
        'date_ajout': '2026-05-10T12:00:00Z',
        'description': 'Un beau terrain à vendre',
        'document_hash': '0xabc123',
        'blockchain_tx_hash': '0xdef456',
        'certificat': {
          'hash_blockchain': '0xabc123',
          'date_validation': '2026-05-10T12:00:00Z',
        },
      };

      final detail = ParcelDetail.fromJson(json);
      expect(detail, isA<ParcelDetail>());
      expect(detail.description, 'Un beau terrain à vendre');
      expect(detail.documentHash, '0xabc123');
      expect(detail.blockchainTxHash, '0xdef456');
      expect(detail.certificat, isNotNull);
      expect(detail.certificat!.hashBlockchain, '0xabc123');
    });
  });

  group('CertificatInfo', () {
    test('devrait être créé depuis JSON', () {
      final json = {
        'hash_blockchain': '0x123',
        'date_validation': '2026-01-01T00:00:00Z',
      };
      final info = CertificatInfo.fromJson(json);
      expect(info.hashBlockchain, '0x123');
      expect(info.dateValidation, DateTime.utc(2026, 1, 1));
    });
  });

  group('ParcelsResponse', () {
    test('devrait être créé depuis JSON', () {
      final json = {
        'count': 1,
        'results': [
          {
            'id': 'p1',
            'titre': 'Test',
            'localisation': 'Dakar',
            'region': 'Dakar',
            'superficie': 100,
            'prix': 5000000,
            'type_terrain': 'residentiel',
            'statut': 'pending',
            'vendeur_nom': 'T',
            'date_ajout': '2026-01-01T00:00:00Z',
          },
        ],
      };
      final response = ParcelsResponse.fromJson(json);
      expect(response.count, 1);
      expect(response.results.length, 1);
      expect(response.results.first.id, 'p1');
    });
  });
}
