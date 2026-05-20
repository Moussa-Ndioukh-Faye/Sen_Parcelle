// lib/features/parcels/presentation/screens/publier_screen.dart
// ═════════════════════════════════════════════════════════════
// Screen pour publier une parcelle avec carte GPS

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';

class PublierScreen extends ConsumerStatefulWidget {
  const PublierScreen({super.key});

  @override
  ConsumerState<PublierScreen> createState() => _PublierScreenState();
}

class _PublierScreenState extends ConsumerState<PublierScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titreController = TextEditingController();
  final _descController = TextEditingController();
  final _localisationController = TextEditingController();
  final _superficieController = TextEditingController();
  final _prixController = TextEditingController();

  LatLng? _selectedLocation;
  bool _isLoading = false;

  final List<String> _regions = [
    'Dakar', 'Thiès', 'Saint-Louis', 'Ziguinchor',
    'Kaolack', 'Diourbel', 'Louga', 'Fatick',
    'Kolda', 'Tambacounda', 'Kaffrine', 'Matam',
    'Kédougou', 'Sédhiou',
  ];
  String _selectedRegion = 'Dakar';

  final List<String> _types = [
    'residentiel', 'commercial', 'agricole', 'industriel',
  ];
  String _selectedType = 'residentiel';

  @override
  void initState() {
    super.initState();
    _getCurrentLocation();
  }

  Future<void> _getCurrentLocation() async {
    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
      setState(() {
        _selectedLocation = LatLng(position.latitude, position.longitude);
      });
    } catch (e) {
      // Fallback sur Dakar
      setState(() {
        _selectedLocation = LatLng(14.6928, -17.4467);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Publier une parcelle')),
      body: SafeArea(
        child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Localisation sur la carte',
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              _buildMap(),
              const SizedBox(height: 16),
              TextFormField(
                controller: _titreController,
                decoration: const InputDecoration(
                  labelText: 'Titre de la parcelle',
                  border: OutlineInputBorder(),
                ),
                validator: (v) => v!.isEmpty ? 'Requis' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _localisationController,
                decoration: const InputDecoration(
                  labelText: 'Adresse / Localisation précise',
                  border: OutlineInputBorder(),
                ),
                validator: (v) => v!.isEmpty ? 'Requis' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _descController,
                decoration: const InputDecoration(
                  labelText: 'Description',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _superficieController,
                      decoration: const InputDecoration(
                        labelText: 'Surface (m²)',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                      validator: (v) => v!.isEmpty ? 'Requis' : null,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _prixController,
                      decoration: const InputDecoration(
                        labelText: 'Prix (FCFA)',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                      validator: (v) => v!.isEmpty ? 'Requis' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _selectedRegion,
                      decoration: const InputDecoration(
                        labelText: 'Région',
                        border: OutlineInputBorder(),
                      ),
                      items: _regions
                          .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                          .toList(),
                      onChanged: (v) => setState(() => _selectedRegion = v!),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _selectedType,
                      decoration: const InputDecoration(
                        labelText: 'Type de terrain',
                        border: OutlineInputBorder(),
                      ),
                      items: _types
                          .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                          .toList(),
                      onChanged: (v) => setState(() => _selectedType = v!),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Publier la parcelle'),
                ),
              ),
            ],
          ),
        ),
      ),
      ),
    );
  }

  Widget _buildMap() {
    return Container(
      height: 300,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: FlutterMap(
          options: MapOptions(
            initialCenter: _selectedLocation ?? LatLng(14.6928, -17.4467),
            initialZoom: 13,
            onTap: (tapPosition, point) {
              setState(() => _selectedLocation = point);
            },
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.example.sen_parcelle',
            ),
            if (_selectedLocation != null)
              MarkerLayer(
                markers: [
                  Marker(
                    point: _selectedLocation!,
                    width: 40,
                    height: 40,
                    child: const Icon(
                      Icons.location_on,
                      color: AppTheme.red,
                      size: 40,
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedLocation == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Veuillez remplir tous les champs et sélectionner un lieu'),
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    // Simuler l'envoi (à connecter au repository)
    await Future.delayed(const Duration(seconds: 2));

    setState(() => _isLoading = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Parcelle publiée avec succès !'),
          backgroundColor: AppTheme.green,
        ),
      );
      Navigator.pop(context);
    }
  }

  @override
  void dispose() {
    _titreController.dispose();
    _descController.dispose();
    _localisationController.dispose();
    _superficieController.dispose();
    _prixController.dispose();
    super.dispose();
  }
}
