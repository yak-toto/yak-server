import Vuex from 'vuex';

import {
  postSignup, postLogin, getGroupNames, getGroup, postMatch, getScoreBoard,
} from '@/api';
import { isValidJwt } from '@/utils';

const state = {
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
    context.commit('setUserData', { userData });
    return postLogin(userData)
      .then((response) => context.commit('setJwtToken', { jwt: response.data }))
      .catch((error) => {
        console.log('Error Authenticating: ', error);
      });
  },
  signup(context, userData) {
    context.commit('setUserData', { userData });
    return postSignup(userData)
      .then((_) => context.dispatch('login', userData))
      .catch((error) => {
        console.log('Error Registering: ', error);
      });
  },
  logout(context) {
    context.commit('eraseJwtToken');
  },
};

const mutations = {
  setUserData(state, payload) {
    state.userData = payload.userData;
  },
  setJwtToken(state, payload) {
    localStorage.token = payload.jwt.token;
    state.jwt = payload.jwt;
  },
  eraseJwtToken(state) {
    localStorage.token = 'deleted';
    state.jwt = 'deleted';
  },
};

const getters = {
  // reusable data accessors
  isAuthenticated(state) {
    return isValidJwt(state.jwt.token);
  },
};

const store = new Vuex.Store({
  state,
  actions,
  mutations,
  getters,
});

export default store;
