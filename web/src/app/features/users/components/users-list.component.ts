// src/app/features/users/components/users-list.component.ts
// ══════════════════════════════════════════════════════════════

import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UsersService } from '../services/users.service';

@Component({
  selector: 'app-users-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="users-container">
      <h2>Utilisateurs</h2>
      @if (users$ | async; as users) {
        <div class="users-table">
          <table>
            <thead>
              <tr>
                <th>Nom</th>
                <th>Email</th>
                <th>Rôle</th>
                <th>KYC</th>
              </tr>
            </thead>
            <tbody>
              @for (user of users; track user.id) {
                <tr>
                  <td>{{ user.nom }}</td>
                  <td>{{ user.email }}</td>
                  <td>{{ user.role }}</td>
                  <td>{{ user.kyc_status || 'N/A' }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      } @else {
        <p>Chargement...</p>
      }
    </div>
  `,
  styles: [`
    .users-container { padding: 24px; }
    .users-table { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
    th { background-color: #f5f5f5; font-weight: 600; }
  `]
})
export class UsersListComponent implements OnInit {
  private usersService = inject(UsersService);
  users$ = this.usersService.getUsers();

  ngOnInit() {}
}
