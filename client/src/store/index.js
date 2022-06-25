import Vuex from 'vuex';
import VuexPersistence from 'vuex-persist';

import {
  postSignup, postLogin, getGroupNames, getGroup, postMatch, getScoreBoard,
} from '@/api';
import { isValidJwt } from '@/utils';

const state = {
  userName: '',
  jwt: '',
};

const actions = {
  getGroup(context, { groupName }) {
    return getGroup(groupName, context.state.jwt.token);
  },
  postMatch(context, { matchId, matchResource }) {
    return postMatch(matchId, matchResource, context.state.jwt.token);
  },
  getScoreBoard(context) {
    return getScoreBoard(context.state.jwt.token);
  },
  getGroupNames(context) {
    return getGroupNames(context.state.jwt.token);
  },
  login(context, userData) {
    return postLogin(userData);
  },
  signup(context, userData) {
    return postSignup(userData);
  },
  logout(context) {
    context.commit('eraseJwtToken');
  },
};

const mutations = {
  setUserName(state, payload) {
    state.userName = payload.userName;
  },
  setJwtToken(state, payload) {
    state.jwt = payload.jwt;
  },
  eraseJwtToken(state) {
    state.jwt = 'deleted';
    state.userName = '';
  },
};

const getters = {
  isAuthenticated(state) {
    return isValidJwt(state.jwt.token);
  },
  getUserName(state) {
    return state.userName;
  },
};

const vuexPersist = new VuexPersistence({
  key: 'myStorage',
  reducer: (state) => state,
});

const store = new Vuex.Store({
  state,
  actions,
  mutations,
  getters,
  plugins: [vuexPersist.plugin],
});

export default store;
