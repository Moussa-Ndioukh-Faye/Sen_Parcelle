// lib/features/parcels/presentation/screens/home_screen.dart
// ═══════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';
import 'package:sen_parcelle/shared/widgets/parcel_card.dart';
import 'package:sen_parcelle/shared/widgets/shimmer_card.dart';
import 'package:sen_parcelle/features/parcels/presentation/providers/parcel_providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final parcelsAsync = ref.watch(parcelsProvider(const {}));

    return Scaffold(
      body: RefreshIndicator(
        color: AppTheme.green,
        onRefresh: () async => ref.invalidate(parcelsProvider),
        child: CustomScrollView(
          slivers: [
            // ─── SliverAppBar Hero ───
            SliverAppBar(
              expandedHeight: 210,
              pinned: true,
              backgroundColor: AppTheme.greenDark,
              flexibleSpace: FlexibleSpaceBar(
                background: Container(
                  decoration: AppTheme.gradientDecoration(),
                  child: SafeArea(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(children: [
                            const CircleAvatar(
                              backgroundColor: Colors.white24,
                              child: Text('M', style: TextStyle(
                                color: Colors.white, fontWeight: FontWeight.bold)),
                            ),
                            const SizedBox(width: 10),
                            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text('Bonjour', style: TextStyle(color: Colors.white70, fontSize: 12)),
                              Text('Moussa Faye', style: TextStyle(
                                color: Colors.white, fontWeight: FontWeight.bold)),
                            ]),
                            const Spacer(),
                            IconButton(
                              icon: const Icon(Icons.notifications_outlined, color: Colors.white),
                              onPressed: () {},
                            ),
                          ]),
                          const SizedBox(height: 12),
                          Text('Trouvez votre terrain\nidéal',
                            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              color: Colors.white, height: 1.2,
                            )),
                          const SizedBox(height: 14),
                          // ─── Barre de recherche ───
                          GestureDetector(
                            onTap: () => context.push('/explore'),
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16, vertical: 12),
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.25)),
                              ),
                              child: Row(children: [
                                const Icon(Icons.search, color: Colors.white70, size: 20),
                                const SizedBox(width: 10),
                                Text('Rechercher une parcelle...',
                                  style: TextStyle(color: Colors.white60, fontSize: 14)),
                              ]),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),

            // ─── Chips filtres ───
            SliverToBoxAdapter(
              child: SizedBox(
                height: 48,
                child: ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  scrollDirection: Axis.horizontal,
                  itemCount: _filters.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (_, i) => FilterChip(
                    label: Text(_filters[i]),
                    selected: i == 0,
                    onSelected: (_) {},
                  ),
                ),
              ),
            ),

            // ─── Section titre ───
            const SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.fromLTRB(16, 8, 16, 12),
                child: Row(children: [
                  Text('Parcelles certifiées',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
                  SizedBox(width: 4),
                  Icon(Icons.verified, size: 16, color: AppTheme.green),
                  Spacer(),
                  Text('Voir tout', style: TextStyle(color: AppTheme.green, fontWeight: FontWeight.w600)),
                ]),
              ),
            ),

            // ─── Liste ───
            parcelsAsync.when(
              loading: () => SliverList(
                delegate: SliverChildBuilderDelegate(
                  (_, __) => const ShimmerCard(height: 200),
                  childCount: 3,
                ),
              ),
              error: (e, _) => SliverToBoxAdapter(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(children: [
                      const Icon(Icons.sentiment_dissatisfied, size: 40, color: AppTheme.muted),
                      const SizedBox(height: 8),
                      Text(e.toString(), textAlign: TextAlign.center,
                        style: TextStyle(color: AppTheme.muted)),
                      const SizedBox(height: 16),
                      TextButton(
                        onPressed: () => ref.invalidate(parcelsProvider),
                        child: const Text('Réessayer'),
                      ),
                    ]),
                  ),
                ),
              ),
              data: (response) => SliverPadding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (ctx, i) => ParcelCard(
                      parcel: response.results[i],
                      onTap:  () => ctx.push('/parcelle/${response.results[i].id}'),
                    ),
                    childCount: response.results.length,
                  ),
                ),
              ),
            ),

            const SliverToBoxAdapter(child: SizedBox(height: 80)),
          ],
        ),
      ),
    );
  }

  static const _filters = ['Tous', 'Dakar', 'Thiès', 'Saint-Louis', 'Agricole', 'Résidentiel'];
}


// ═══════════════════════════════════════════════════════════════