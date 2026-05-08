// lib/features/parcels/presentation/screens/explore_screen.dart
// ═══════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/shared/widgets/parcel_card.dart';
import 'package:sen_parcelle/shared/widgets/shimmer_card.dart';
import 'package:sen_parcelle/shared/widgets/gradient_button.dart';
import 'package:sen_parcelle/features/parcels/presentation/providers/parcel_providers.dart';

class ExploreScreen extends ConsumerStatefulWidget {
  const ExploreScreen({super.key});
  @override ConsumerState<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends ConsumerState<ExploreScreen> {
  final _searchCtrl = TextEditingController();
  String? _selectedRegion;
  String? _selectedType;
  RangeValues _priceRange = const RangeValues(0, 500000000);

  static const _regions = ['Dakar','Thiès','Saint-Louis','Ziguinchor','Kaolack'];
  static const _types   = ['residentiel','commercial','agricole','industriel'];

  @override
  Widget build(BuildContext context) {
    final params = <String, dynamic>{
      if (_selectedRegion != null) 'region': _selectedRegion,
      if (_selectedType   != null) 'type_terrain': _selectedType,
      if (_searchCtrl.text.isNotEmpty) 'search': _searchCtrl.text,
      'min_price': _priceRange.start,
      'max_price': _priceRange.end,
    };
    final parcelsAsync = ref.watch(parcelsProvider(params));

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          controller: _searchCtrl,
          decoration: const InputDecoration(
            hintText: 'Rechercher...',
            border: InputBorder.none,
            prefixIcon: Icon(Icons.search, color: Colors.white70),
            hintStyle: TextStyle(color: Colors.white60),
          ),
          style: const TextStyle(color: Colors.white),
          onChanged: (_) => setState(() {}),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            onPressed: () => _showFilters(context),
          ),
        ],
      ),
      body: Column(children: [
        // ─── Chips régions ───
        SizedBox(
          height: 46,
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            scrollDirection: Axis.horizontal,
            itemCount: _regions.length + 1,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (_, i) {
              if (i == 0) return FilterChip(
                label: const Text('Toutes'),
                selected: _selectedRegion == null,
                onSelected: (_) => setState(() => _selectedRegion = null),
              );
              final r = _regions[i - 1];
              return FilterChip(
                label: Text(r),
                selected: _selectedRegion == r,
                onSelected: (_) => setState(() => _selectedRegion = r),
              );
            },
          ),
        ),

        // ─── Résultats ───
        Expanded(child: parcelsAsync.when(
          loading: () => ListView.builder(
            itemCount: 3,
            itemBuilder: (_, __) => const ShimmerCard(height: 200),
          ),
          error: (e, _) => Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.sentiment_dissatisfied, size: 40, color: AppTheme.muted),
              const SizedBox(height: 8),
              Text('$e', style: const TextStyle(color: AppTheme.muted)),
              TextButton(
                onPressed: () => ref.invalidate(parcelsProvider),
                child: const Text('Réessayer'),
              ),
            ]),
          ),
          data: (r) => r.results.isEmpty
            ? const Center(child: Text('Aucune parcelle trouvée'))
            : ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: r.results.length,
                itemBuilder: (ctx, i) => ParcelCard(
                  parcel: r.results[i],
                  onTap:  () => ctx.push('/parcelle/${r.results[i].id}'),
                ),
              ),
        )),
      ]),
    );
  }

  void _showFilters(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('Filtres', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          const Align(alignment: Alignment.centerLeft,
            child: Text('Type de terrain', style: TextStyle(fontWeight: FontWeight.w600))),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8, runSpacing: 8,
            children: _types.map((t) => FilterChip(
              label: Text(t),
              selected: _selectedType == t,
              onSelected: (_) => setState(() => _selectedType = _selectedType == t ? null : t),
            )).toList(),
          ),
          const SizedBox(height: 24),
          GradientButton(
            label: 'Appliquer',
            onPressed: () { Navigator.pop(context); setState(() {}); },
          ),
        ]),
      ),
    );
  }
}