import { createRouter, createWebHistory } from 'vue-router';
import LoginComponent from '@/components/LoginComponent.vue';
import GroupComponent from '@/components/GroupComponent.vue';
import SignupComponent from '@/components/SignupComponent.vue';
import ScoreBoardComponent from '@/components/ScoreBoardComponent.vue';
import store from '@/store';

const routes = [
  {
    path: '/',
    name: 'home',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'login',
    component: LoginComponent,
  },
  {
    path: '/signup',
    name: 'signup',
    component: SignupComponent,
  },
  {
    path: '/logout',
    name: 'logout',
    beforeEnter(to, from, next) {
      if (store.getters.isAuthenticated) {
        store.commit('eraseJwtToken');
      }
      next('/login');
    },
  },
  {
    path: '/groups/:groupName',
    name: 'groups',
    component: GroupComponent,
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

router.beforeEach((to, from, next) => {
  if (to.name !== 'login' && to.name !== 'signup' && !store.getters.isAuthenticated) {
    store.commit('eraseJwtToken');
    next({ name: 'login' });
  } else next();
});

export default router;
