// api/index.js

import axios from 'axios';

const URL = 'http://127.0.0.1:5000';
const GLOBAL_ENDPOINT = 'yak_toto';
const VERSION = 'v1';

// ------------------------------
// Auth interface
// ------------------------------

export function postSignup(userData) {
  return axios.post(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/signup`, userData);
}

export function postLogin(userData) {
  return axios.post(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/login`, userData);
}

// ------------------------------
// Group interface
// ------------------------------

export function getGroupNames(jwt) {
  return axios.get(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/groups/names`, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function getGroup(groupName, jwt) {
  return axios.get(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/groups/${groupName}`, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function postMatch(matchId, matchResource, jwt) {
  return axios.post(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/match/${matchId}`, matchResource, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function getMatch(team1, team2) {
  return axios.get(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/match`, { params: { team1, team2 } });
}

// ------------------------------
// Result interface
// ------------------------------

export function getScoreBoard(jwt) {
  return axios.get(`${URL}/${GLOBAL_ENDPOINT}/${VERSION}/score_board`, { headers: { Authorization: `Bearer: ${jwt}` } });
}
