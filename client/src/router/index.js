import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@/views/HomeView.vue';
import LoginComponent from '@/components/LoginComponent.vue';
import GroupComponent from '@/components/GroupComponent.vue';
import SignupComponent from '@/components/SignupComponent.vue';
import ScoreBoardComponent from '@/components/ScoreBoardComponent.vue';
import LogoutComponent from '@/components/LogoutComponent.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginComponent,
  },
  {
    path: '/groups/:group_name',
    name: 'groups',
    component: GroupComponent,
  },
  {
    path: '/signup',
    name: 'signup',
    component: SignupComponent,
  },
  {
    path: '/logout',
    name: 'logout',
    component: LogoutComponent,
  },
  {
    path: '/score_board',
    name: 'score_board',
    component: ScoreBoardComponent,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
